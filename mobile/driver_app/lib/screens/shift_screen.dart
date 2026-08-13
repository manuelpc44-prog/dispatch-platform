import 'dart:async';

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../models/vehicle.dart';
import '../providers/auth_provider.dart';
import '../providers/shift_provider.dart';
import '../repositories/vehicle_repository.dart';
import '../services/gps_tracking_service.dart';

class ShiftScreen extends StatefulWidget {
  const ShiftScreen({super.key});

  @override
  State<ShiftScreen> createState() => _ShiftScreenState();
}

class _ShiftScreenState extends State<ShiftScreen> {
  List<Vehicle>? _vehicles;
  String? _selectedVehicleId;
  String? _loadError;
  StreamSubscription<GpsConnectionState>? _stateSub;
  GpsConnectionState _gpsState = GpsConnectionState.gpsDisabled;
  Timer? _pendingTimer;

  @override
  void initState() {
    super.initState();
    _loadVehicles();
    final shift = context.read<ShiftProvider>();
    _stateSub = shift.trackingService.stateStream.listen((s) {
      if (mounted) setState(() => _gpsState = s);
    });
    _pendingTimer = Timer.periodic(const Duration(seconds: 5), (_) {
      context.read<ShiftProvider>().refreshPendingCount();
    });
  }

  @override
  void dispose() {
    _stateSub?.cancel();
    _pendingTimer?.cancel();
    super.dispose();
  }

  Future<void> _loadVehicles() async {
    try {
      final apiClient = context.read<AuthProvider>().apiClient;
      final vehicles = await VehicleRepository(apiClient).list();
      if (mounted) {
        setState(() {
          _vehicles = vehicles;
          _selectedVehicleId = vehicles.isNotEmpty ? vehicles.first.id : null;
        });
      }
    } catch (e) {
      if (mounted) setState(() => _loadError = e.toString());
    }
  }

  @override
  Widget build(BuildContext context) {
    final shift = context.watch<ShiftProvider>();

    return Scaffold(
      backgroundColor: const Color(0xFF14181F),
      appBar: AppBar(
        backgroundColor: const Color(0xFF1C222C),
        title: const Text('Jornada'),
      ),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: shift.isActive ? _buildActiveState(shift) : _buildIdleState(shift),
        ),
      ),
    );
  }

  Widget _buildIdleState(ShiftProvider shift) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        const Text(
          'Selecciona tu vehículo para iniciar la jornada',
          style: TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.w600),
        ),
        const SizedBox(height: 16),
        if (_loadError != null)
          Text(_loadError!, style: const TextStyle(color: Color(0xFFFF6B5B))),
        if (_vehicles == null && _loadError == null)
          const Center(child: CircularProgressIndicator(color: Color(0xFFF5A623))),
        if (_vehicles != null)
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 12),
            decoration: BoxDecoration(
              color: const Color(0xFF1C222C),
              borderRadius: BorderRadius.circular(8),
              border: Border.all(color: const Color(0xFF2A303C)),
            ),
            child: DropdownButtonHideUnderline(
              child: DropdownButton<String>(
                value: _selectedVehicleId,
                isExpanded: true,
                dropdownColor: const Color(0xFF1C222C),
                style: const TextStyle(color: Colors.white),
                items: _vehicles!
                    .map((v) => DropdownMenuItem(value: v.id, child: Text(v.label)))
                    .toList(),
                onChanged: (value) => setState(() => _selectedVehicleId = value),
              ),
            ),
          ),
        const SizedBox(height: 24),
        if (shift.errorMessage != null) ...[
          Text(shift.errorMessage!, style: const TextStyle(color: Color(0xFFFF6B5B), fontSize: 13)),
          const SizedBox(height: 12),
        ],
        ElevatedButton(
          onPressed: (_selectedVehicleId == null ||
                  shift.uiState == ShiftUiState.requestingPermissions ||
                  shift.uiState == ShiftUiState.starting)
              ? null
              : () => shift.startShift(_selectedVehicleId!),
          style: ElevatedButton.styleFrom(
            backgroundColor: const Color(0xFFF5A623),
            foregroundColor: const Color(0xFF1A1204),
            padding: const EdgeInsets.symmetric(vertical: 16),
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
          ),
          child: Text(
            _labelForStartButton(shift.uiState),
            style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 15),
          ),
        ),
      ],
    );
  }

  String _labelForStartButton(ShiftUiState state) {
    switch (state) {
      case ShiftUiState.requestingPermissions:
        return 'Solicitando permisos…';
      case ShiftUiState.starting:
        return 'Iniciando jornada…';
      default:
        return 'INICIAR JORNADA';
    }
  }

  Widget _buildActiveState(ShiftProvider shift) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: const Color(0xFF1C222C),
            borderRadius: BorderRadius.circular(10),
            border: Border.all(color: const Color(0xFF2A303C)),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  _pulseDot(),
                  const SizedBox(width: 10),
                  const Text('Jornada activa', style: TextStyle(color: Colors.white, fontWeight: FontWeight.w700)),
                ],
              ),
              const SizedBox(height: 12),
              _statusRow('Señal GPS', _gpsStateLabel(_gpsState)),
              _statusRow('Posiciones sin sincronizar', '${shift.pendingInQueue}'),
            ],
          ),
        ),
        const Spacer(),
        if (shift.errorMessage != null) ...[
          Text(shift.errorMessage!, style: const TextStyle(color: Color(0xFFFF6B5B), fontSize: 12)),
          const SizedBox(height: 12),
        ],
        ElevatedButton(
          onPressed: shift.uiState == ShiftUiState.ending ? null : () => shift.endShift(),
          style: ElevatedButton.styleFrom(
            backgroundColor: const Color(0xFFFF6B5B),
            foregroundColor: Colors.white,
            padding: const EdgeInsets.symmetric(vertical: 16),
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
          ),
          child: Text(
            shift.uiState == ShiftUiState.ending ? 'Finalizando…' : 'FINALIZAR JORNADA',
            style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 15),
          ),
        ),
      ],
    );
  }

  Widget _pulseDot() {
    return Container(
      width: 10,
      height: 10,
      decoration: const BoxDecoration(color: Color(0xFFF5A623), shape: BoxShape.circle),
    );
  }

  Widget _statusRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: const TextStyle(color: Color(0xFF8B93A3), fontSize: 13)),
          Text(value, style: const TextStyle(color: Colors.white, fontSize: 13, fontFamily: 'monospace')),
        ],
      ),
    );
  }

  String _gpsStateLabel(GpsConnectionState state) {
    switch (state) {
      case GpsConnectionState.online:
        return 'ONLINE';
      case GpsConnectionState.offline:
        return 'OFFLINE';
      case GpsConnectionState.gpsDisabled:
        return 'GPS_DISABLED';
      case GpsConnectionState.gpsActive:
        return 'GPS_ACTIVE';
      case GpsConnectionState.lowAccuracy:
        return 'LOW_ACCURACY';
    }
  }
}
