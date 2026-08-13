class DeliveryEvidenceItem {
  final String tipo; // FIRMA o FOTO
  final String url;
  DeliveryEvidenceItem({required this.tipo, required this.url});

  Map<String, dynamic> toJson() => {'tipo': tipo, 'url': url};
}

class DeliveryResultPayload {
  final String shipmentId;
  final String resultado; // ENTREGADO o NO_ENTREGADO
  final String? receptorNombre;
  final String? motivoFallo;
  final String? observacion;
  final double? gpsLat;
  final double? gpsLng;
  final List<DeliveryEvidenceItem> evidence;

  DeliveryResultPayload({
    required this.shipmentId,
    required this.resultado,
    this.receptorNombre,
    this.motivoFallo,
    this.observacion,
    this.gpsLat,
    this.gpsLng,
    this.evidence = const [],
  });

  Map<String, dynamic> toJson() => {
        'shipment_id': shipmentId,
        'resultado': resultado,
        if (receptorNombre != null) 'receptor_nombre': receptorNombre,
        if (motivoFallo != null) 'motivo_fallo': motivoFallo,
        if (observacion != null) 'observacion': observacion,
        if (gpsLat != null) 'gps_lat': gpsLat,
        if (gpsLng != null) 'gps_lng': gpsLng,
        'evidence': evidence.map((e) => e.toJson()).toList(),
      };
}
