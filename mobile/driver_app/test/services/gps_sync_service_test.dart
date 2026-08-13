import 'package:flutter_test/flutter_test.dart';
import 'package:driver_app/services/gps_sync_service.dart';
import 'package:driver_app/services/local_gps_queue.dart';
import 'package:driver_app/services/api_client.dart';

/// NOTA: no pudo ejecutarse en este entorno (sin Dart SDK, ver README.md).
/// flush() con la cola vacía es la única aserción segura sin mockear Dio;
/// para probar el camino con red simulada haría falta un adapter mock de
/// Dio (dio_adapter o similar) — no incluido aquí por alcance de tiempo.
void main() {
  test('flush con la cola vacía no falla y devuelve 0', () async {
    final apiClient = ApiClient();
    final queue = LocalGpsQueue();
    final syncService = GpsSyncService(apiClient, queue);

    final result = await syncService.flush();
    expect(result, 0);
  });
}
