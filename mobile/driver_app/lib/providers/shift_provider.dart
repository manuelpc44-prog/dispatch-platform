import 'package:flutter/foundation.dart';

import '../models/driver_shift.dart';
import '../repositories/shift_repository.dart';
import '../services/api_client.dart';
import '../services/gps_sync_service.dart';
import '../services/gps_tracking_service.dart';
import '../services/local_gps_queue.dart';

enum ShiftUiState { idle, requestingPermissions, starting, active, ending }

class ShiftProvider extends ChangeNotifier {
  final ShiftRepository _shiftRepository;
  final GpsTrackingService trackingService;
  final GpsSyncService syncService;
  final LocalGpsQueue queue;

  ShiftProvider(ApiClient apiClient)
      : _shiftRepository = ShiftRepository(apiClient),
        queue = _sharedQueue,
        trackingService = GpsTrackingService(_sharedQueue),
        syncService = GpsSyncService(apiClient, _sharedQueue);

  static final LocalGpsQueue _sharedQueue = LocalGpsQueue();

  ShiftUiState uiState = ShiftUiState.idle;
  DriverShift? currentShift;
  String? errorMessage;
  int pendingInQueue = 0;

  bool get isActive => currentShift?.isActive ?? false;

  Future<bool> startShift(String vehicleId) async {
    uiState = ShiftUiState.requestingPermissions;
    errorMessage = null;
    notifyListeners();

    final permission = await trackingService.requestPermissions();
    if (!permission.granted) {
      errorMessage = permission.reason ?? 'No se otorgaron los permisos de ubicación';
      uiState = ShiftUiState.idle;
      notifyListeners();
      return false;
    }
    if (!permission.backgroundGranted) {
      // No bloqueamos el inicio de jornada por esto — se lo advertimos al
      // chofer en la UI, porque sin permiso "todo el tiempo" el tracking se
      // detendrá cuando la app pase a segundo plano prolongadamente.
      errorMessage = 'Ubicación en segundo plano no concedida — el tracking podría '
          'interrumpirse si sales de la app. Actívala en Ajustes para mayor '
          'confiabilidad.';
    }

    uiState = ShiftUiState.starting;
    notifyListeners();

    try {
      final shift = await _shiftRepository.start(vehicleId);
      currentShift = shift;
      await trackingService.start(shift.id);
      syncService.start();
      uiState = ShiftUiState.active;
      notifyListeners();
      return true;
    } catch (e) {
      errorMessage = e.toString();
      uiState = ShiftUiState.idle;
      notifyListeners();
      return false;
    }
  }

  Future<bool> endShift() async {
    if (currentShift == null) return false;
    uiState = ShiftUiState.ending;
    notifyListeners();

    try {
      // Flush final ANTES de detener el tracking, para no perder las últimas
      // posiciones encoladas (ver docs/gps.md sección 20).
      await syncService.flush();
      await trackingService.stop();
      syncService.stop();

      final shift = await _shiftRepository.end(currentShift!.id);
      currentShift = shift;
      uiState = ShiftUiState.idle;
      notifyListeners();
      return true;
    } catch (e) {
      errorMessage = e.toString();
      uiState = ShiftUiState.active; // seguía activa, se puede reintentar finalizar
      notifyListeners();
      return false;
    }
  }

  Future<void> refreshPendingCount() async {
    pendingInQueue = await queue.countPending();
    notifyListeners();
  }

  @override
  void dispose() {
    trackingService.dispose();
    syncService.stop();
    super.dispose();
  }
}
