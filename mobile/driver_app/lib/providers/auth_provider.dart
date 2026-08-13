import 'package:flutter/foundation.dart';

import '../models/auth_user.dart';
import '../repositories/auth_repository.dart';
import '../services/api_client.dart';
import '../services/push_notification_service.dart';

enum AuthStatus { unknown, authenticated, unauthenticated }

class AuthProvider extends ChangeNotifier {
  final AuthRepository _authRepository;
  final ApiClient apiClient;

  AuthProvider(this.apiClient) : _authRepository = AuthRepository(apiClient);

  AuthStatus status = AuthStatus.unknown;
  AuthUser? user;
  String? errorMessage;
  bool isLoading = false;

  Future<void> bootstrap() async {
    final hasSession = await apiClient.hasSession();
    if (!hasSession) {
      status = AuthStatus.unauthenticated;
      notifyListeners();
      return;
    }
    try {
      user = await _authRepository.me();
      status = AuthStatus.authenticated;
    } catch (_) {
      status = AuthStatus.unauthenticated;
    }
    notifyListeners();
  }

  Future<bool> login(String email, String password) async {
    isLoading = true;
    errorMessage = null;
    notifyListeners();
    try {
      user = await _authRepository.login(email, password);
      status = AuthStatus.authenticated;
      _registerPushTokenSilently();
      return true;
    } catch (e) {
      errorMessage = e.toString();
      status = AuthStatus.unauthenticated;
      return false;
    } finally {
      isLoading = false;
      notifyListeners();
    }
  }

  /// No bloquea el login si Firebase no está configurado o falla — el
  /// registro del token es best-effort (ver docs/gps.md filosofía similar
  /// para GPS: nunca romper el flujo principal por una dependencia externa).
  void _registerPushTokenSilently() {
    PushNotificationService(apiClient).registerDeviceToken().catchError((_) {});
  }

  Future<void> logout() async {
    await _authRepository.logout();
    user = null;
    status = AuthStatus.unauthenticated;
    notifyListeners();
  }
}
