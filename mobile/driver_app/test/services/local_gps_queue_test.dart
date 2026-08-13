import 'package:flutter_test/flutter_test.dart';
import 'package:sqflite_common_ffi/sqflite_ffi.dart';
import 'package:driver_app/services/local_gps_queue.dart';

/// NOTA: este archivo no pudo ejecutarse en el entorno de desarrollo usado
/// para este proyecto (sin Dart SDK disponible, ver README.md de esta app).
/// Requiere el paquete de dev `sqflite_common_ffi` para correr sin un
/// dispositivo/emulador real — agregar a pubspec.yaml en dev_dependencies
/// antes de ejecutar `flutter test`.
void main() {
  setUpAll(() {
    sqfliteFfiInit();
    databaseFactory = databaseFactoryFfi;
  });

  late LocalGpsQueue queue;

  setUp(() {
    queue = LocalGpsQueue();
  });

  test('enqueue agrega una posición pendiente', () async {
    await queue.enqueue(
      clientUuid: 'uuid-1',
      driverShiftId: 'shift-1',
      latitude: -33.5,
      longitude: -70.6,
      recordedAt: DateTime.now().toUtc().toIso8601String(),
    );

    final pending = await queue.getPending();
    expect(pending.length, 1);
    expect(pending.first['client_uuid'], 'uuid-1');
  });

  test('enqueue con el mismo client_uuid no duplica (idempotencia local)', () async {
    final recordedAt = DateTime.now().toUtc().toIso8601String();
    await queue.enqueue(
      clientUuid: 'uuid-dup', driverShiftId: 'shift-1',
      latitude: -33.5, longitude: -70.6, recordedAt: recordedAt,
    );
    await queue.enqueue(
      clientUuid: 'uuid-dup', driverShiftId: 'shift-1',
      latitude: -33.6, longitude: -70.7, recordedAt: recordedAt,
    );

    final pending = await queue.getPending();
    final matching = pending.where((p) => p['client_uuid'] == 'uuid-dup');
    expect(matching.length, 1);
  });

  test('markSynced saca las posiciones de "pendientes"', () async {
    await queue.enqueue(
      clientUuid: 'uuid-2', driverShiftId: 'shift-1',
      latitude: -33.5, longitude: -70.6,
      recordedAt: DateTime.now().toUtc().toIso8601String(),
    );

    await queue.markSynced(['uuid-2']);
    final pending = await queue.getPending();
    expect(pending.where((p) => p['client_uuid'] == 'uuid-2'), isEmpty);
  });

  test('countPending refleja solo lo no sincronizado', () async {
    await queue.enqueue(
      clientUuid: 'uuid-3', driverShiftId: 'shift-1',
      latitude: -33.5, longitude: -70.6,
      recordedAt: DateTime.now().toUtc().toIso8601String(),
    );
    await queue.enqueue(
      clientUuid: 'uuid-4', driverShiftId: 'shift-1',
      latitude: -33.5, longitude: -70.6,
      recordedAt: DateTime.now().toUtc().toIso8601String(),
    );
    await queue.markSynced(['uuid-3']);

    final count = await queue.countPending();
    expect(count, 1);
  });
}
