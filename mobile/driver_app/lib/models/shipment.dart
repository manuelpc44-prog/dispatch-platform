class Shipment {
  final String id;
  final String numero;
  final String trackingCode;
  final String customerId;
  final String addressId;
  final String warehouseId;
  final String? driverId;
  final String? vehicleId;
  final String fechaProgramada;
  final String? horaProgramada;
  final String prioridad;
  final String estado;
  final String? observaciones;

  Shipment({
    required this.id,
    required this.numero,
    required this.trackingCode,
    required this.customerId,
    required this.addressId,
    required this.warehouseId,
    required this.driverId,
    required this.vehicleId,
    required this.fechaProgramada,
    required this.horaProgramada,
    required this.prioridad,
    required this.estado,
    required this.observaciones,
  });

  factory Shipment.fromJson(Map<String, dynamic> json) {
    return Shipment(
      id: json['id'] as String,
      numero: json['numero'] as String,
      trackingCode: json['tracking_code'] as String,
      customerId: json['customer_id'] as String,
      addressId: json['address_id'] as String,
      warehouseId: json['warehouse_id'] as String,
      driverId: json['driver_id'] as String?,
      vehicleId: json['vehicle_id'] as String?,
      fechaProgramada: json['fecha_programada'] as String,
      horaProgramada: json['hora_programada'] as String?,
      prioridad: json['prioridad'] as String,
      estado: json['estado'] as String,
      observaciones: json['observaciones'] as String?,
    );
  }
}
