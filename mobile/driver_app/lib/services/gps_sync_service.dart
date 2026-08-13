import 'dart:async';

import '../services/api_client.dart';
import 'local_gps_queue.dart';

/// Sincroniza la cola offline con el backend (POST /tracking/location).
/// Se ejecuta periódicamente mientras la jornada está activa; también se
/// puede forzar un flush final al terminar la jornada.
class GpsSyncService {
  final ApiClient apiClient;
  final LocalGpsQueue queue;
  Timer? _timer;

  GpsSyncService(this.apiClient, this.queue);

  void start({Duration interval = const Duration(seconds: 20)}) {
    _timer?.cancel();
    _timer = Timer.periodic(interval, (_) => flush());
  }

  void stop() {
    _timer?.cancel();
    _timer = null;
  }

  /// Envía las posiciones pendientes al backend. Devuelve la cantidad
  /// efectivamente confirmada (insertada o detectada como duplicado — ambos
  /// casos significan que el backend ya la tiene, así que se marca local
  /// como sincronizada).
  Future<int> flush() async {
    final pending = await queue.getPending(limit: 200);
    if (pending.isEmpty) return 0;

    final positions = pending
        .map((row) => {
              'client_uuid': row['client_uuid'],
              'latitude': row['latitude'],
              'longitude': row['longitude'],
              'accuracy': row['accuracy'],
              'speed': row['speed'],
              'heading': row['heading'],
              'battery_level': row['battery_level'],
              'network_status': row['network_status'],
              'recorded_at': row['recorded_at'],
            })
        .toList();

    try {
      final resp = await apiClient.dio.post('/tracking/location', data: {'positions': positions});
      if (resp.statusCode == 200) {
        final clientUuids = pending.map((row) => row['client_uuid'] as String).toList();
        await queue.markSynced(clientUuids);
        return clientUuids.length;
      }
      return 0;
    } catch (_) {
      // Sin red o error del servidor: las posiciones quedan en la cola local
      // para el próximo intento. Nunca se pierden (ver docs/gps.md sección 20).
      return 0;
    }
  }
}
