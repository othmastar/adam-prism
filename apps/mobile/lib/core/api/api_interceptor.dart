import 'dart:convert';
import 'package:http/http.dart' as http;

class ApiInterceptor {
  ApiInterceptor._();

  static http.BaseRequest intercept(http.BaseRequest request) {
    // Add common headers
    request.headers['Accept'] = 'application/json';
    request.headers['Content-Type'] = 'application/json';
    return request;
  }

  static ApiException handleError(http.Response response) {
    try {
      final body = jsonDecode(response.body) as Map<String, dynamic>;
      final message = body['detail'] as String? ??
          body['message'] as String? ??
          body['error'] as String? ??
          'Unknown error';
      return ApiException(message, statusCode: response.statusCode);
    } catch (_) {
      return ApiException(
        'Request failed with status ${response.statusCode}',
        statusCode: response.statusCode,
        body: response.body,
      );
    }
  }
}

class ApiException implements Exception {
  final String message;
  final int? statusCode;
  final String? body;

  ApiException(this.message, {this.statusCode, this.body});

  @override
  String toString() => 'ApiException: $message (status: $statusCode)';
}
