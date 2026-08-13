import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

/// Base URL configurable por variable de entorno de build
/// (--dart-define=API_BASE_URL=https://tu-servidor/api). Por defecto apunta al
/// backend local para desarrollo con el emulador Android (10.0.2.2 = localhost
/// del host desde el emulador).
const String _defaultBaseUrl = String.fromEnvironment(
  'API_BASE_URL',
  defaultValue: 'http://10.0.2.2:8000/api',
);

class ApiException implements Exception {
  final int? statusCode;
  final String message;
  final String? code;
  ApiException(this.statusCode, this.message, [this.code]);

  @override
  String toString() => message;
}

class ApiClient {
  static const _storage = FlutterSecureStorage();
  static const _accessKey = 'access_token';
  static const _refreshKey = 'refresh_token';

  late final Dio dio;

  ApiClient({String baseUrl = _defaultBaseUrl}) {
    dio = Dio(BaseOptions(baseUrl: baseUrl, connectTimeout: const Duration(seconds: 10)));

    dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) async {
        final token = await _storage.read(key: _accessKey);
        if (token != null) {
          options.headers['Authorization'] = 'Bearer $token';
        }
        handler.next(options);
      },
      onError: (error, handler) async {
        if (error.response?.statusCode == 401) {
          final refreshed = await _tryRefresh();
          if (refreshed) {
            final retryReq = error.requestOptions;
            final token = await _storage.read(key: _accessKey);
            retryReq.headers['Authorization'] = 'Bearer $token';
            try {
              final response = await dio.fetch(retryReq);
              return handler.resolve(response);
            } catch (_) {
              // cae al error original si el reintento también falla
            }
          } else {
            await clearTokens();
          }
        }
        handler.next(_mapError(error));
      },
    ));
  }

  DioException _mapError(DioException error) {
    final data = error.response?.data;
    String message = 'Error de conexión';
    String? code;
    if (data is Map && data['detail'] is Map) {
      final detail = data['detail'] as Map;
      if (detail['error'] is Map) {
        message = detail['error']['message'] ?? message;
        code = detail['error']['code'];
      }
    }
    return DioException(
      requestOptions: error.requestOptions,
      response: error.response,
      error: ApiException(error.response?.statusCode, message, code),
      type: error.type,
    );
  }

  Future<bool> _tryRefresh() async {
    final refreshToken = await _storage.read(key: _refreshKey);
    if (refreshToken == null) return false;
    try {
      final resp = await Dio(BaseOptions(baseUrl: dio.options.baseUrl)).post(
        '/auth/refresh',
        data: {'refresh_token': refreshToken},
      );
      await _storage.write(key: _accessKey, value: resp.data['access_token']);
      await _storage.write(key: _refreshKey, value: resp.data['refresh_token']);
      return true;
    } catch (_) {
      return false;
    }
  }

  Future<void> saveTokens(String accessToken, String refreshToken) async {
    await _storage.write(key: _accessKey, value: accessToken);
    await _storage.write(key: _refreshKey, value: refreshToken);
  }

  Future<void> clearTokens() async {
    await _storage.delete(key: _accessKey);
    await _storage.delete(key: _refreshKey);
  }

  Future<String?> getAccessToken() => _storage.read(key: _accessKey);

  Future<bool> hasSession() async => (await _storage.read(key: _accessKey)) != null;
}
