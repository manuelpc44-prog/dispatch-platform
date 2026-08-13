import 'dart:io';

import 'package:flutter/material.dart';
import 'package:geolocator/geolocator.dart';
import 'package:image_picker/image_picker.dart';
import 'package:provider/provider.dart';
import 'package:signature/signature.dart';

import '../models/delivery.dart';
import '../providers/auth_provider.dart';
import '../repositories/delivery_repository.dart';

class DeliveryScreen extends StatefulWidget {
  final String shipmentId;
  final String shipmentNumero;
  const DeliveryScreen({super.key, required this.shipmentId, required this.shipmentNumero});

  @override
  State<DeliveryScreen> createState() => _DeliveryScreenState();
}

class _DeliveryScreenState extends State<DeliveryScreen> {
  late final DeliveryRepository _repo;
  final _receptorController = TextEditingController();
  final _observacionController = TextEditingController();
  final _signatureController = SignatureController(penColor: Colors.black, penStrokeWidth: 3);

  File? _photo;
  bool _submitting = false;
  String? _error;
  bool _entregaExitosa = true;
  String? _motivoSeleccionado;
  List<String> _motivos = [];

  @override
  void initState() {
    super.initState();
    _repo = DeliveryRepository(context.read<AuthProvider>().apiClient);
    _repo.listMotivosNoEntrega().then((m) {
      if (mounted) setState(() => _motivos = m);
    }).catchError((_) {});
  }

  Future<void> _pickPhoto() async {
    final picked = await ImagePicker().pickImage(source: ImageSource.camera, imageQuality: 80);
    if (picked != null) setState(() => _photo = File(picked.path));
  }

  Future<void> _submit() async {
    setState(() {
      _submitting = true;
      _error = null;
    });
    try {
      Position? position;
      try {
        position = await Geolocator.getCurrentPosition();
      } catch (_) {
        // Sin fix de GPS disponible al momento de entregar — se registra sin
        // coordenadas antes que bloquear la entrega completa.
      }

      final evidence = <DeliveryEvidenceItem>[];

      if (_entregaExitosa && !_signatureController.isEmpty) {
        final signatureBytes = await _signatureController.toPngBytes();
        if (signatureBytes != null) {
          final tempFile = File(
            '${Directory.systemTemp.path}/firma_${DateTime.now().millisecondsSinceEpoch}.png',
          );
          await tempFile.writeAsBytes(signatureBytes);
          final url = await _repo.uploadEvidence(tempFile);
          evidence.add(DeliveryEvidenceItem(tipo: 'FIRMA', url: url));
        }
      }

      if (_photo != null) {
        final url = await _repo.uploadEvidence(_photo!);
        evidence.add(DeliveryEvidenceItem(tipo: 'FOTO', url: url));
      }

      await _repo.registerDelivery(DeliveryResultPayload(
        shipmentId: widget.shipmentId,
        resultado: _entregaExitosa ? 'ENTREGADO' : 'NO_ENTREGADO',
        receptorNombre: _entregaExitosa ? _receptorController.text : null,
        motivoFallo: _entregaExitosa ? null : _motivoSeleccionado,
        observacion: _observacionController.text.isEmpty ? null : _observacionController.text,
        gpsLat: position?.latitude,
        gpsLng: position?.longitude,
        evidence: evidence,
      ));

      if (mounted) Navigator.of(context).pop(true);
    } catch (e) {
      if (mounted) setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _submitting = false);
    }
  }

  @override
  void dispose() {
    _receptorController.dispose();
    _observacionController.dispose();
    _signatureController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF14181F),
      appBar: AppBar(
        backgroundColor: const Color(0xFF1C222C),
        title: Text('Entrega — ${widget.shipmentNumero}'),
      ),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(20),
          children: [
            _resultToggle(),
            const SizedBox(height: 20),
            if (_entregaExitosa) ..._buildEntregaExitosaForm() else ..._buildEntregaFallidaForm(),
            const SizedBox(height: 16),
            TextField(
              controller: _observacionController,
              style: const TextStyle(color: Colors.white),
              maxLines: 2,
              decoration: _decoration('Observación (opcional)'),
            ),
            if (_error != null) ...[
              const SizedBox(height: 12),
              Text(_error!, style: const TextStyle(color: Color(0xFFFF6B5B))),
            ],
            const SizedBox(height: 24),
            ElevatedButton(
              onPressed: _submitting ? null : _submit,
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFFF5A623),
                foregroundColor: const Color(0xFF1A1204),
                padding: const EdgeInsets.symmetric(vertical: 16),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
              ),
              child: Text(
                _submitting ? 'Guardando…' : 'CONFIRMAR ENTREGA',
                style: const TextStyle(fontWeight: FontWeight.w700),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _resultToggle() {
    return Row(
      children: [
        Expanded(
          child: _toggleButton('Entregado', _entregaExitosa, () => setState(() => _entregaExitosa = true)),
        ),
        const SizedBox(width: 10),
        Expanded(
          child: _toggleButton('No entregado', !_entregaExitosa, () => setState(() => _entregaExitosa = false)),
        ),
      ],
    );
  }

  Widget _toggleButton(String label, bool selected, VoidCallback onTap) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 12),
        decoration: BoxDecoration(
          color: selected ? const Color(0xFFF5A623).withOpacity(0.15) : const Color(0xFF1C222C),
          border: Border.all(color: selected ? const Color(0xFFF5A623) : const Color(0xFF2A303C)),
          borderRadius: BorderRadius.circular(8),
        ),
        alignment: Alignment.center,
        child: Text(
          label,
          style: TextStyle(
            color: selected ? const Color(0xFFF5A623) : const Color(0xFF8B93A3),
            fontWeight: FontWeight.w600,
          ),
        ),
      ),
    );
  }

  List<Widget> _buildEntregaExitosaForm() {
    return [
      TextField(
        controller: _receptorController,
        style: const TextStyle(color: Colors.white),
        decoration: _decoration('Nombre de quien recibe'),
      ),
      const SizedBox(height: 16),
      const Text('Firma', style: TextStyle(color: Color(0xFF8B93A3), fontSize: 12)),
      const SizedBox(height: 6),
      Container(
        height: 160,
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(8),
          border: Border.all(color: const Color(0xFF2A303C)),
        ),
        child: Signature(controller: _signatureController, backgroundColor: Colors.white),
      ),
      Align(
        alignment: Alignment.centerRight,
        child: TextButton(
          onPressed: () => _signatureController.clear(),
          child: const Text('Limpiar firma', style: TextStyle(color: Color(0xFF8B93A3))),
        ),
      ),
      const SizedBox(height: 8),
      const Text('Fotografía', style: TextStyle(color: Color(0xFF8B93A3), fontSize: 12)),
      const SizedBox(height: 6),
      GestureDetector(
        onTap: _pickPhoto,
        child: Container(
          height: 140,
          decoration: BoxDecoration(
            color: const Color(0xFF1C222C),
            borderRadius: BorderRadius.circular(8),
            border: Border.all(color: const Color(0xFF2A303C)),
          ),
          child: _photo == null
              ? const Center(
                  child: Icon(Icons.camera_alt_outlined, color: Color(0xFF8B93A3), size: 32),
                )
              : ClipRRect(
                  borderRadius: BorderRadius.circular(8),
                  child: Image.file(_photo!, fit: BoxFit.cover, width: double.infinity),
                ),
        ),
      ),
    ];
  }

  List<Widget> _buildEntregaFallidaForm() {
    return [
      const Text('Motivo', style: TextStyle(color: Color(0xFF8B93A3), fontSize: 12)),
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
            value: _motivoSeleccionado,
            isExpanded: true,
            hint: const Text('Selecciona un motivo', style: TextStyle(color: Color(0xFF8B93A3))),
            dropdownColor: const Color(0xFF1C222C),
            style: const TextStyle(color: Colors.white),
            items: _motivos.map((m) => DropdownMenuItem(value: m, child: Text(m))).toList(),
            onChanged: (value) => setState(() => _motivoSeleccionado = value),
          ),
        ),
      ),
      const SizedBox(height: 8),
      GestureDetector(
        onTap: _pickPhoto,
        child: Container(
          height: 120,
          margin: const EdgeInsets.only(top: 8),
          decoration: BoxDecoration(
            color: const Color(0xFF1C222C),
            borderRadius: BorderRadius.circular(8),
            border: Border.all(color: const Color(0xFF2A303C)),
          ),
          child: _photo == null
              ? const Center(
                  child: Icon(Icons.camera_alt_outlined, color: Color(0xFF8B93A3), size: 28),
                )
              : ClipRRect(
                  borderRadius: BorderRadius.circular(8),
                  child: Image.file(_photo!, fit: BoxFit.cover, width: double.infinity),
                ),
        ),
      ),
    ];
  }

  InputDecoration _decoration(String label) {
    return InputDecoration(
      labelText: label,
      labelStyle: const TextStyle(color: Color(0xFF8B93A3)),
      filled: true,
      fillColor: const Color(0xFF1C222C),
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(8),
        borderSide: const BorderSide(color: Color(0xFF2A303C)),
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(8),
        borderSide: const BorderSide(color: Color(0xFF2A303C)),
      ),
    );
  }
}
