import 'package:path/path.dart';
import 'package:sqflite/sqflite.dart';

/// Cola local de posiciones GPS. Cada posición generada en el dispositivo se
/// guarda aquí PRIMERO (nunca se pierde aunque no haya red), y se marca como
/// sincronizada solo cuando el backend confirma la recepción (ver
/// docs/gps.md sección 20: "GPS sin Internet").
class LocalGpsQueue {
  static Database? _db;

  Future<Database> get _database async {
    if (_db != null) return _db!;
    _db = await _open();
    return _db!;
  }

  Future<Database> _open() async {
    final path = join(await getDatabasesPath(), 'gps_queue.db');
    return openDatabase(
      path,
      version: 1,
      onCreate: (db, version) async {
        await db.execute('''
          CREATE TABLE gps_queue (
            client_uuid TEXT PRIMARY KEY,
            driver_shift_id TEXT,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            accuracy REAL,
            speed REAL,
            heading REAL,
            battery_level INTEGER,
            network_status TEXT,
            recorded_at TEXT NOT NULL,
            synced INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL
          )
        ''');
        await db.execute('CREATE INDEX idx_gps_queue_synced ON gps_queue (synced)');
      },
    );
  }

  Future<void> enqueue({
    required String clientUuid,
    required String driverShiftId,
    required double latitude,
    required double longitude,
    double? accuracy,
    double? speed,
    double? heading,
    int? batteryLevel,
    String? networkStatus,
    required String recordedAt,
  }) async {
    final db = await _database;
    await db.insert(
      'gps_queue',
      {
        'client_uuid': clientUuid,
        'driver_shift_id': driverShiftId,
        'latitude': latitude,
        'longitude': longitude,
        'accuracy': accuracy,
        'speed': speed,
        'heading': heading,
        'battery_level': batteryLevel,
        'network_status': networkStatus,
        'recorded_at': recordedAt,
        'synced': 0,
        'created_at': DateTime.now().toUtc().toIso8601String(),
      },
      // client_uuid es la clave primaria: si por algún motivo se genera dos
      // veces el mismo (no debería pasar, uuid v4), no duplica la fila local.
      conflictAlgorithm: ConflictAlgorithm.ignore,
    );
  }

  /// Devuelve hasta [limit] posiciones no sincronizadas, en orden cronológico.
  Future<List<Map<String, Object?>>> getPending({int limit = 100}) async {
    final db = await _database;
    return db.query(
      'gps_queue',
      where: 'synced = 0',
      orderBy: 'recorded_at ASC',
      limit: limit,
    );
  }

  /// Marca como sincronizadas las posiciones cuyo client_uuid fue confirmado
  /// por el backend. No se borran de inmediato (se conservan un tiempo para
  /// diagnóstico); ver [purgeSynced] para limpieza periódica.
  Future<void> markSynced(List<String> clientUuids) async {
    if (clientUuids.isEmpty) return;
    final db = await _database;
    final placeholders = List.filled(clientUuids.length, '?').join(',');
    await db.rawUpdate(
      'UPDATE gps_queue SET synced = 1 WHERE client_uuid IN ($placeholders)',
      clientUuids,
    );
  }

  /// Purga posiciones ya sincronizadas y con más de [olderThan] de antigüedad,
  /// para no crecer indefinidamente en el dispositivo.
  Future<void> purgeSynced({Duration olderThan = const Duration(days: 3)}) async {
    final db = await _database;
    final cutoff = DateTime.now().toUtc().subtract(olderThan).toIso8601String();
    await db.delete(
      'gps_queue',
      where: 'synced = 1 AND created_at < ?',
      whereArgs: [cutoff],
    );
  }

  Future<int> countPending() async {
    final db = await _database;
    final result = await db.rawQuery('SELECT COUNT(*) as c FROM gps_queue WHERE synced = 0');
    return Sqflite.firstIntValue(result) ?? 0;
  }
}
