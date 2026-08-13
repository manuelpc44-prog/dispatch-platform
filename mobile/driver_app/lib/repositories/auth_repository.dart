import '../models/auth_user.dart';
import '../services/api_client.dart';

class AuthRepository {
  final ApiClient apiClient;
  AuthRepository(this.apiClient);

  Future<AuthUser> login(String email, String password) async {
    final resp = await apiClient.dio.post(
      '/auth/login',
      data: {'email': email, 'password': password},
    );
    await apiClient.saveTokens(resp.data['access_token'], resp.data['refresh_token']);
    return me();
  }

  Future<AuthUser> me() async {
    final resp = await apiClient.dio.get('/auth/me');
    return AuthUser.fromJson(resp.data as Map<String, dynamic>);
  }

  Future<void> logout() => apiClient.clearTokens();
}
