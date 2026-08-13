class DriverShift {
  final String id;
  final String driverId;
  final String vehicleId;
  final String estado;
  final String? iniciadaAt;
  final String? finalizadaAt;

  DriverShift({
    required this.id,
    required this.driverId,
    required this.vehicleId,
    required this.estado,
    required this.iniciadaAt,
    required this.finalizadaAt,
  });

  factory DriverShift.fromJson(Map<String, dynamic> json) {
    return DriverShift(
      id: json['id'] as String,
      driverId: json['driver_id'] as String,
      vehicleId: json['vehicle_id'] as String,
      estado: json['estado'] as String,
      iniciadaAt: json['iniciada_at'] as String?,
      finalizadaAt: json['finalizada_at'] as String?,
    );
  }

  bool get isActive => estado == 'INICIADA' || estado == 'EN_RUTA' || estado == 'REGRESANDO';
}
