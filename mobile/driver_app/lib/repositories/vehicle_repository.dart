import '../models/vehicle.dart';
import '../services/api_client.dart';

class VehicleRepository {
  final ApiClient apiClient;
  VehicleRepository(this.apiClient);

  Future<List<Vehicle>> list() async {
    final resp = await apiClient.dio.get('/vehicles', queryParameters: {'limit': 100});
    return (resp.data as List)
        .map((json) => Vehicle.fromJson(json as Map<String, dynamic>))
        .toList();
  }
}
