import 'package:firebase_messaging/firebase_messaging.dart';

import 'api_client.dart';

/// Registra el token FCM del dispositivo contra el backend
/// (POST /notifications/register-device, ver Fase 14 backend).
///
/// REQUIERE, antes de poder inicializar Firebase en la app:
///   1. Un proyecto Firebase real (ver instrucciones completas en
///      backend/app/services/push_service.py).
///   2. Descargar `google-services.json` desde Firebase Console
///      (Configuración del proyecto > Tus apps > app Android) y colocarlo en
///      `android/app/google-services.json`.
///   3. Agregar el plugin de Google Services al build de Android:
///      - android/build.gradle: classpath 'com.google.gms:google-services:4.4.2'
///      - android/app/build.gradle: apply plugin: 'com.google.gms.google-services'
///      (no se editó aquí el build.gradle real porque este proyecto Flutter
///      nunca se generó con `flutter create` en este sandbox — no hay
///      android/build.gradle base sobre el cual aplicar el cambio con
///      confianza sin verlo. Hacerlo en la primera corrida con Flutter real.)
///   4. Llamar `Firebase.initializeApp()` en `main()` ANTES de `runApp()`.
class PushNotificationService {
  final ApiClient apiClient;
  PushNotificationService(this.apiClient);

  Future<void> registerDeviceToken() async {
    final messaging = FirebaseMessaging.instance;
    await messaging.requestPermission();

    final token = await messaging.getToken();
    if (token == null) return;

    await apiClient.dio.post('/notifications/register-device', data: {
      'token': token,
      'platform': 'android',
    });

    // Si el token rota (puede pasar), reenviarlo automáticamente.
    FirebaseMessaging.instance.onTokenRefresh.listen((newToken) {
      apiClient.dio.post('/notifications/register-device', data: {
        'token': newToken,
        'platform': 'android',
      });
    });
  }
}
