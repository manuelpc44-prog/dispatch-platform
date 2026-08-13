import 'package:flutter/material.dart';

const Map<String, Color> _statusColors = {
  'CREADO': Color(0xFF8B93A3),
  'PENDIENTE': Color(0xFF8B93A3),
  'PREPARANDO': Color(0xFF5B9DFF),
  'LISTO': Color(0xFF5B9DFF),
  'ASIGNADO': Color(0xFFF5A623),
  'SALIDA_BODEGA': Color(0xFFF5A623),
  'EN_RUTA': Color(0xFFF5A623),
  'LLEGADA_CLIENTE': Color(0xFFF5A623),
  'ENTREGA_EN_PROCESO': Color(0xFFF5A623),
  'ENTREGADO': Color(0xFF2DD4A7),
  'NO_ENTREGADO': Color(0xFFFF6B5B),
  'INCIDENCIA': Color(0xFFFF6B5B),
  'REGRESO_BODEGA': Color(0xFFF5A623),
  'LLEGADA_BODEGA': Color(0xFF2DD4A7),
  'COMPLETADO': Color(0xFF2DD4A7),
  'CANCELADO': Color(0xFF8B93A3),
};

class StatusBadge extends StatelessWidget {
  final String status;
  const StatusBadge({super.key, required this.status});

  @override
  Widget build(BuildContext context) {
    final color = _statusColors[status] ?? const Color(0xFF8B93A3);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: color.withOpacity(0.12),
        borderRadius: BorderRadius.circular(999),
        border: Border.all(color: color.withOpacity(0.4)),
      ),
      child: Text(
        status,
        style: TextStyle(
          color: color,
          fontSize: 11,
          fontFamily: 'monospace',
          fontWeight: FontWeight.w600,
        ),
      ),
    );
  }
}
