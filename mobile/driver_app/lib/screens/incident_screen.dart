import 'package:flutter/material.dart';
import 'package:geolocator/geolocator.dart';
import 'package:provider/provider.dart';

import '../providers/auth_provider.dart';
import '../repositories/delivery_repository.dart';

const _tiposIncidencia = [
  'Cliente ausente',
  'Dirección incorrecta',
  'Cliente rechazó',
  'Problema de acceso',
  'Problema vehículo',
  'Otro',
];

class IncidentScreen extends StatefulWidget {
  final String shipmentId;
  final String shipmentNumero;
  const IncidentScreen({super.key, required this.shipmentId, required this.shipmentNumero});

  @override
  State<IncidentScreen> createState() => _IncidentScreenState();
}

class _IncidentScreenState extends State<IncidentScreen> {
  late final DeliveryRepository _repo;
  String? _tipo;
  final _descripcionController = TextEditingController();
  bool _submitting = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _repo = DeliveryRepository(context.read<AuthProvider>().apiClient);
  }

  Future<void> _submit() async {
    if (_tipo == null) {
      setState(() => _error = 'Selecciona un tipo de incidencia');
      return;
    }
    setState(() {
      _submitting = true;
      _error = null;
    });
    try {
      Position? position;
      try {
        position = await Geolocator.getCurrentPosition();
      } catch (_) {
        /* se registra sin GPS si no hay fix disponible */
      }
      await _repo.reportIncident(
        shipmentId: widget.shipmentId,
        tipo: _tipo!,
        descripcion: _descripcionController.text.isEmpty ? null : _descripcionController.text,
        gpsLat: position?.latitude,
        gpsLng: position?.longitude,
      );
      if (mounted) Navigator.of(context).pop(true);
    } catch (e) {
      if (mounted) setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _submitting = false);
    }
  }

  @override
  void dispose() {
    _descripcionController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF14181F),
      appBar: AppBar(
        backgroundColor: const Color(0xFF1C222C),
        title: Text('Incidencia — ${widget.shipmentNumero}'),
      ),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const Text('Tipo de incidencia', style: TextStyle(color: Color(0xFF8B93A3), fontSize: 12)),
              const SizedBox(height: 6),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 12),
                decoration: BoxDecoration(
                  color: const Color(0xFF1C222C),
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: const Color(0xFF2A303C)),
                ),
                child: DropdownButtonHideUnderline(
                  child: DropdownButton<String>(
                    value: _tipo,
                    isExpanded: true,
                    hint: const Text('Selecciona…', style: TextStyle(color: Color(0xFF8B93A3))),
                    dropdownColor: const Color(0xFF1C222C),
                    style: const TextStyle(color: Colors.white),
                    items: _tiposIncidencia
                        .map((t) => DropdownMenuItem(value: t, child: Text(t)))
                        .toList(),
                    onChanged: (value) => setState(() => _tipo = value),
                  ),
                ),
              ),
              const SizedBox(height: 16),
              TextField(
                controller: _descripcionController,
                style: const TextStyle(color: Colors.white),
                maxLines: 3,
                decoration: InputDecoration(
                  labelText: 'Descripción (opcional)',
                  labelStyle: const TextStyle(color: Color(0xFF8B93A3)),
                  filled: true,
                  fillColor: const Color(0xFF1C222C),
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(8),
                    borderSide: const BorderSide(color: Color(0xFF2A303C)),
                  ),
                ),
              ),
              if (_error != null) ...[
                const SizedBox(height: 12),
                Text(_error!, style: const TextStyle(color: Color(0xFFFF6B5B))),
              ],
              const SizedBox(height: 24),
              ElevatedButton(
                onPressed: _submitting ? null : _submit,
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFFFF6B5B),
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(vertical: 16),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                ),
                child: Text(
                  _submitting ? 'Enviando…' : 'REPORTAR INCIDENCIA',
                  style: const TextStyle(fontWeight: FontWeight.w700),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
