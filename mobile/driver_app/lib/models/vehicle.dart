class Vehicle {
  final String id;
  final String plate;
  final String? brand;
  final String? model;

  Vehicle({required this.id, required this.plate, this.brand, this.model});

  factory Vehicle.fromJson(Map<String, dynamic> json) {
    return Vehicle(
      id: json['id'] as String,
      plate: json['plate'] as String,
      brand: json['brand'] as String?,
      model: json['model'] as String?,
    );
  }

  String get label => '$plate${brand != null ? ' — $brand $model' : ''}';
}
