import '../models/shipment.dart';
import '../services/api_client.dart';

class ShipmentRepository {
  final ApiClient apiClient;
  ShipmentRepository(this.apiClient);

  /// Lista los despachos visibles para el usuario autenticado. Para un CHOFER,
  /// el backend hoy no filtra por driver_id (eso llega en Fase 11 cuando exista
  /// jornada activa); mientras tanto la app filtra localmente por driver_id
  /// cuando corresponde, para no mostrarle despachos ajenos en la UI.
  Future<List<Shipment>> listMine({String? driverId}) async {
    final resp = await apiClient.dio.get('/shipments', queryParameters: {'limit': 100});
    final all = (resp.data as List)
        .map((json) => Shipment.fromJson(json as Map<String, dynamic>))
        .toList();
    if (driverId == null) return all;
    return all.where((s) => s.driverId == driverId).toList();
  }
}
