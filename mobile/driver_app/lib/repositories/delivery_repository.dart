import 'dart:io';

import 'package:dio/dio.dart';

import '../models/delivery.dart';
import '../services/api_client.dart';

class DeliveryRepository {
  final ApiClient apiClient;
  DeliveryRepository(this.apiClient);

  Future<List<String>> listMotivosNoEntrega() async {
    final resp = await apiClient.dio.get('/deliveries/motivos-no-entrega');
    return (resp.data as List).map((e) => e as String).toList();
  }

  /// Sube un archivo (foto o firma exportada como PNG) y devuelve la URL
  /// relativa que el backend asigna (servida desde /media, ver Fase 12).
  Future<String> uploadEvidence(File file) async {
    final formData = FormData.fromMap({
      'file': await MultipartFile.fromFile(file.path, filename: file.path.split('/').last),
    });
    final resp = await apiClient.dio.post('/deliveries/evidence', data: formData);
    return resp.data['url'] as String;
  }

  Future<void> registerDelivery(DeliveryResultPayload payload) async {
    await apiClient.dio.post('/deliveries', data: payload.toJson());
  }

  Future<void> reportIncident({
    required String shipmentId,
    required String tipo,
    String? descripcion,
    double? gpsLat,
    double? gpsLng,
  }) async {
    await apiClient.dio.post('/incidents', data: {
      'shipment_id': shipmentId,
      'tipo': tipo,
      if (descripcion != null) 'descripcion': descripcion,
      if (gpsLat != null) 'gps_lat': gpsLat,
      if (gpsLng != null) 'gps_lng': gpsLng,
    });
  }
}
