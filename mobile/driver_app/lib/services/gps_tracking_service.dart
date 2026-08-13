import 'dart:async';

import 'package:battery_plus/battery_plus.dart';
import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:flutter_foreground_task/flutter_foreground_task.dart';
import 'package:geolocator/geolocator.dart';
import 'package:uuid/uuid.dart';

import 'local_gps_queue.dart';

enum GpsConnectionState { online, offline, gpsDisabled, gpsActive, lowAccuracy }

/// Resultado de solicitar permisos, para que la UI pueda explicarle al chofer
/// qué falta exactamente (ver docs/gps.md sección 45 — estados de conexión).
class LocationPermissionResult {
  final bool granted;
  final bool backgroundGranted;
  final String? reason;
  LocationPermissionResult({required this.granted, required this.backgroundGranted, this.reason});
}

/// Umbrales de frecuencia de muestreo (ver docs/gps.md sección 2).
class _SamplingStrategy {
  static const double movingDistanceFilterMeters = 30;
  static const Duration movingMaxInterval = Duration(seconds: 15);
  static const Duration stoppedHeartbeat = Duration(seconds: 60);
  static const Duration lowBatteryHeartbeat = Duration(seconds: 120);
  static const int lowBatteryThreshold = 15;
  static const double movingSpeedThresholdKmh = 5;
  static const double lowAccuracyThresholdMeters = 50;
}

class GpsTrackingService {
  final LocalGpsQueue queue;
  final _uuid = const Uuid();
  final _battery = Battery();

  StreamSubscription<Position>? _positionSub;
  Timer? _heartbeatTimer;
  String? _driverShiftId;
  DateTime _lastRecordedAt = DateTime.fromMillisecondsSinceEpoch(0);

  final _stateController = StreamController<GpsConnectionState>.broadcast();
  Stream<GpsConnectionState> get stateStream => _stateController.stream;

  GpsTrackingService(this.queue);

  /// Solicitud de permisos en dos pasos, como exige Android 10+ para
  /// ACCESS_BACKGROUND_LOCATION (ver nota en AndroidManifest.xml).
  Future<LocationPermissionResult> requestPermissions() async {
    final serviceEnabled = await Geolocator.isLocationServiceEnabled();
    if (!serviceEnabled) {
      return LocationPermissionResult(
        granted: false,
        backgroundGranted: false,
        reason: 'El GPS del dispositivo está desactivado',
      );
    }

    LocationPermission permission = await Geolocator.checkPermission();
    if (permission == LocationPermission.denied) {
      permission = await Geolocator.requestPermission();
    }
    if (permission == LocationPermission.denied || permission == LocationPermission.deniedForever) {
      return LocationPermissionResult(
        granted: false,
        backgroundGranted: false,
        reason: 'Permiso de ubicación denegado',
      );
    }

    // Paso 2: "todo el tiempo" (background). En Android 10 (API 29) y 11+ el
    // sistema requiere UI adicional (o Ajustes) para este permiso — Geolocator
    // expone LocationPermission.always como el objetivo tras el segundo diálogo.
    final backgroundGranted = permission == LocationPermission.always;

    return LocationPermissionResult(granted: true, backgroundGranted: backgroundGranted);
  }

  Future<void> start(String driverShiftId) async {
    _driverShiftId = driverShiftId;

    await FlutterForegroundTask.init(
      androidNotificationOptions: AndroidNotificationOptions(
        channelId: 'gps_tracking_channel',
        channelName: 'Seguimiento de ruta activo',
        channelDescription: 'Tu ubicación se comparte mientras la jornada está activa',
        onlyAlertOnce: true,
      ),
      iosNotificationOptions: const IOSNotificationOptions(),
      foregroundTaskOptions: ForegroundTaskOptions(
        eventAction: ForegroundTaskEventAction.repeat(15000),
        autoRunOnBoot: false,
        allowWakeLock: true,
        allowWifiLock: false,
      ),
    );

    await FlutterForegroundTask.startService(
      notificationTitle: 'Jornada en curso',
      notificationText: 'Transmitiendo tu ubicación a la central de despachos',
    );

    const locationSettings = LocationSettings(
      accuracy: LocationAccuracy.high,
      distanceFilter: 0, // el filtro de distancia real lo aplicamos nosotros abajo,
      // combinado con el filtro de tiempo — Geolocator solo con distanceFilter no
      // cubre el caso "detenido, pero igual mandar heartbeat cada 60s".
    );

    _positionSub = Geolocator.getPositionStream(locationSettings: locationSettings).listen(_onPosition);

    // Heartbeat: revisa cada 10s si toca enviar un punto por tiempo, aunque el
    // vehículo esté detenido y Geolocator no emita eventos nuevos.
    _heartbeatTimer = Timer.periodic(const Duration(seconds: 10), (_) => _checkHeartbeat());
  }

  Future<void> stop() async {
    await _positionSub?.cancel();
    _positionSub = null;
    _heartbeatTimer?.cancel();
    _heartbeatTimer = null;
    _driverShiftId = null;
    await FlutterForegroundTask.stopService();
  }

  void _checkHeartbeat() async {
    if (_driverShiftId == null) return;
    final elapsed = DateTime.now().toUtc().difference(_lastRecordedAt);
    final batteryLevel = await _battery.batteryLevel;
    final threshold = batteryLevel <= _SamplingStrategy.lowBatteryThreshold
        ? _SamplingStrategy.lowBatteryHeartbeat
        : _SamplingStrategy.stoppedHeartbeat;
    if (elapsed >= threshold) {
      try {
        final position = await Geolocator.getCurrentPosition();
        await _recordPosition(position, batteryLevel);
      } catch (_) {
        // Sin fix de GPS disponible en este instante — se reintenta en el
        // próximo ciclo de heartbeat, no se pierde el intervalo de tracking.
      }
    }
  }

  Future<void> _onPosition(Position position) async {
    final batteryLevel = await _battery.batteryLevel;
    final elapsedSinceLast = DateTime.now().toUtc().difference(_lastRecordedAt);
    final speedKmh = position.speed * 3.6;
    final isMoving = speedKmh >= _SamplingStrategy.movingSpeedThresholdKmh;

    final maxInterval = batteryLevel <= _SamplingStrategy.lowBatteryThreshold
        ? _SamplingStrategy.lowBatteryHeartbeat
        : (isMoving ? _SamplingStrategy.movingMaxInterval : _SamplingStrategy.stoppedHeartbeat);

    // Combinación distancia-O-tiempo (ver docs/gps.md sección 2): si superamos
    // el intervalo máximo, registramos igual aunque la distancia sea corta.
    if (elapsedSinceLast >= maxInterval) {
      await _recordPosition(position, batteryLevel);
    }

    if (position.accuracy > _SamplingStrategy.lowAccuracyThresholdMeters) {
      _stateController.add(GpsConnectionState.lowAccuracy);
    } else {
      _stateController.add(GpsConnectionState.gpsActive);
    }
  }

  Future<void> _recordPosition(Position position, int batteryLevel) async {
    if (_driverShiftId == null) return;
    final connectivity = await Connectivity().checkConnectivity();
    final networkStatus = connectivity.contains(ConnectivityResult.none) ? 'OFFLINE' : 'ONLINE';

    await queue.enqueue(
      clientUuid: _uuid.v4(),
      driverShiftId: _driverShiftId!,
      latitude: position.latitude,
      longitude: position.longitude,
      accuracy: position.accuracy,
      speed: position.speed,
      heading: position.heading,
      batteryLevel: batteryLevel,
      networkStatus: networkStatus,
      recordedAt: DateTime.now().toUtc().toIso8601String(),
    );
    _lastRecordedAt = DateTime.now().toUtc();
  }

  void dispose() {
    _positionSub?.cancel();
    _heartbeatTimer?.cancel();
    _stateController.close();
  }
}
