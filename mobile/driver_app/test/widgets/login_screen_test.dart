import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:driver_app/providers/auth_provider.dart';
import 'package:driver_app/screens/login_screen.dart';
import 'package:driver_app/services/api_client.dart';

/// NOTA: no pudo ejecutarse en este entorno (sin Dart SDK, ver README.md).
void main() {
  Widget buildApp() {
    return ChangeNotifierProvider(
      create: (_) => AuthProvider(ApiClient()),
      child: const MaterialApp(home: LoginScreen()),
    );
  }

  testWidgets('muestra campos de correo y contraseña', (tester) async {
    await tester.pumpWidget(buildApp());
    expect(find.byType(TextFormField), findsNWidgets(2));
    expect(find.text('Ingresar'), findsOneWidget);
  });

  testWidgets('valida que el correo no esté vacío', (tester) async {
    await tester.pumpWidget(buildApp());
    await tester.tap(find.text('Ingresar'));
    await tester.pump();
    expect(find.text('Ingresa tu correo'), findsOneWidget);
  });

  testWidgets('valida que la contraseña no esté vacía', (tester) async {
    await tester.pumpWidget(buildApp());
    await tester.enterText(find.byType(TextFormField).first, 'chofer1@dispatchplatform.cl');
    await tester.tap(find.text('Ingresar'));
    await tester.pump();
    expect(find.text('Ingresa tu contraseña'), findsOneWidget);
  });
}
