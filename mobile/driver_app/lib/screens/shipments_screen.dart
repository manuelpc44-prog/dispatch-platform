import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../models/shipment.dart';
import '../providers/auth_provider.dart';
import '../repositories/shipment_repository.dart';
import '../widgets/status_badge.dart';
import 'delivery_screen.dart';
import 'incident_screen.dart';

class ShipmentsScreen extends StatefulWidget {
  const ShipmentsScreen({super.key});

  @override
  State<ShipmentsScreen> createState() => _ShipmentsScreenState();
}

class _ShipmentsScreenState extends State<ShipmentsScreen> {
  late final ShipmentRepository _repo;
  List<Shipment>? _shipments;
  String? _error;

  @override
  void initState() {
    super.initState();
    final apiClient = context.read<AuthProvider>().apiClient;
    _repo = ShipmentRepository(apiClient);
    _load();
  }

  Future<void> _load() async {
    setState(() {
      _error = null;
      _shipments = null;
    });
    try {
      final shipments = await _repo.listMine();
      if (mounted) setState(() => _shipments = shipments);
    } catch (e) {
      if (mounted) setState(() => _error = e.toString());
    }
  }

  bool _canAct(String estado) {
    const activeStates = {
      'SALIDA_BODEGA', 'EN_RUTA', 'LLEGADA_CLIENTE', 'ENTREGA_EN_PROCESO',
    };
    return activeStates.contains(estado);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF14181F),
      appBar: AppBar(
        backgroundColor: const Color(0xFF1C222C),
        title: const Text('Mis despachos'),
      ),
      body: RefreshIndicator(
        onRefresh: _load,
        child: _buildBody(),
      ),
    );
  }

  Widget _buildBody() {
    if (_error != null) {
      return ListView(
        children: [
          Padding(
            padding: const EdgeInsets.all(24),
            child: Text(_error!, style: const TextStyle(color: Color(0xFFFF6B5B))),
          ),
        ],
      );
    }
    if (_shipments == null) {
      return const Center(child: CircularProgressIndicator(color: Color(0xFFF5A623)));
    }
    if (_shipments!.isEmpty) {
      return ListView(
        children: const [
          Padding(
            padding: EdgeInsets.all(24),
            child: Text(
              'No tienes despachos asignados por ahora.',
              style: TextStyle(color: Color(0xFF8B93A3)),
            ),
          ),
        ],
      );
    }
    return ListView.separated(
      padding: const EdgeInsets.all(16),
      itemCount: _shipments!.length,
      separatorBuilder: (_, __) => const SizedBox(height: 10),
      itemBuilder: (context, index) {
        final s = _shipments![index];
        return Container(
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            color: const Color(0xFF1C222C),
            borderRadius: BorderRadius.circular(10),
            border: Border.all(color: const Color(0xFF2A303C)),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    s.numero,
                    style: const TextStyle(
                      color: Colors.white,
                      fontFamily: 'monospace',
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  StatusBadge(status: s.estado),
                ],
              ),
              const SizedBox(height: 6),
              Text(
                'Programado: ${s.fechaProgramada}',
                style: const TextStyle(color: Color(0xFF8B93A3), fontSize: 12),
              ),
              if (s.observaciones != null && s.observaciones!.isNotEmpty) ...[
                const SizedBox(height: 4),
                Text(
                  s.observaciones!,
                  style: const TextStyle(color: Color(0xFF8B93A3), fontSize: 12),
                ),
              ],
              if (_canAct(s.estado)) ...[
                const SizedBox(height: 12),
                Row(
                  children: [
                    if (s.estado == 'ENTREGA_EN_PROCESO')
                      Expanded(
                        child: OutlinedButton(
                          onPressed: () async {
                            final result = await Navigator.of(context).push<bool>(
                              MaterialPageRoute(
                                builder: (_) => DeliveryScreen(shipmentId: s.id, shipmentNumero: s.numero),
                              ),
                            );
                            if (result == true) _load();
                          },
                          style: OutlinedButton.styleFrom(
                            foregroundColor: const Color(0xFFF5A623),
                            side: const BorderSide(color: Color(0xFFF5A623)),
                          ),
                          child: const Text('Entregar'),
                        ),
                      ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: OutlinedButton(
                        onPressed: () async {
                          final result = await Navigator.of(context).push<bool>(
                            MaterialPageRoute(
                              builder: (_) => IncidentScreen(shipmentId: s.id, shipmentNumero: s.numero),
                            ),
                          );
                          if (result == true) _load();
                        },
                        style: OutlinedButton.styleFrom(
                          foregroundColor: const Color(0xFFFF6B5B),
                          side: const BorderSide(color: Color(0xFFFF6B5B)),
                        ),
                        child: const Text('Incidencia'),
                      ),
                    ),
                  ],
                ),
              ],
            ],
          ),
        );
      },
    );
  }
}
