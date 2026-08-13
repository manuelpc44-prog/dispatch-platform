import '../models/driver_shift.dart';
import '../services/api_client.dart';

class ShiftRepository {
  final ApiClient apiClient;
  ShiftRepository(this.apiClient);

  Future<DriverShift> start(String vehicleId, {double? odometroInicio}) async {
    final resp = await apiClient.dio.post('/shifts/start', data: {
      'vehicle_id': vehicleId,
      if (odometroInicio != null) 'odometro_inicio': odometroInicio,
    });
    return DriverShift.fromJson(resp.data as Map<String, dynamic>);
  }

  Future<DriverShift> end(String shiftId, {double? odometroFin}) async {
    final resp = await apiClient.dio.post('/shifts/$shiftId/end', data: {
      if (odometroFin != null) 'odometro_fin': odometroFin,
    });
    return DriverShift.fromJson(resp.data as Map<String, dynamic>);
  }
}
