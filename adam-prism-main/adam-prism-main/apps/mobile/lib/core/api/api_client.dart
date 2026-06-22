import 'dart:convert';
import 'dart:async';
import 'package:http/http.dart' as http;
import '../storage/local_storage.dart';
import '../constants/app_constants.dart';
import 'api_interceptor.dart';
import 'sse_client.dart';

class ApiClient {
  ApiClient._();

  static final ApiClient instance = ApiClient._();

  String _baseUrl = AppConstants.defaultBackendUrl;
  String? _apiKey;
  final http.Client _client = http.Client();

  String get baseUrl => _baseUrl;

  void configure({required String baseUrl, String? apiKey}) {
    _baseUrl = baseUrl.replaceAll(RegExp(r'/+$'), '');
    _apiKey = apiKey;
  }

  Future<void> loadConfig() async {
    _baseUrl = LocalStorage.instance.backendUrl;
    _apiKey = await LocalStorage.instance.apiKey;
  }

  Map<String, String> get _headers => {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    if (_apiKey != null && _apiKey!.isNotEmpty) ...{
      'X-API-Key': _apiKey!,
    },
  };

  Future<T> _handleResponse<T>(
    http.Response response, {
    T Function(Map<String, dynamic>)? fromJson,
  }) async {
    if (response.statusCode >= 200 && response.statusCode < 300) {
      if (response.body.isEmpty) {
        return <String, dynamic>{} as T;
      }
      try {
        final json = jsonDecode(response.body);
        if (json is Map<String, dynamic>) {
          if (fromJson != null) return fromJson(json);
          return json as T;
        }
        return json as T;
      } catch (e) {
        throw ApiException('Failed to parse response: $e');
      }
    } else {
      throw ApiException(
        'Request failed',
        statusCode: response.statusCode,
        body: response.body,
      );
    }
  }

  Future<T> get<T>(
    String path, {
    Map<String, dynamic>? queryParameters,
    T Function(Map<String, dynamic>)? fromJson,
  }) async {
    final uri = Uri.parse('$_baseUrl$path').replace(
      queryParameters: queryParameters?.map(
        (k, v) => MapEntry(k, v.toString()),
      ),
    );
    try {
      final response = await _client
          .get(uri, headers: _headers)
          .timeout(AppConstants.connectionTimeout);
      return _handleResponse(response, fromJson: fromJson);
    } on TimeoutException {
      throw ApiException('Connection timeout');
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException('Network error: $e');
    }
  }

  Future<T> post<T>(
    String path, {
    Map<String, dynamic>? body,
    T Function(Map<String, dynamic>)? fromJson,
  }) async {
    final uri = Uri.parse('$_baseUrl$path');
    try {
      final response = await _client
          .post(uri, headers: _headers, body: jsonEncode(body))
          .timeout(AppConstants.readTimeout);
      return _handleResponse(response, fromJson: fromJson);
    } on TimeoutException {
      throw ApiException('Request timeout');
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException('Network error: $e');
    }
  }

  Future<T> delete<T>(
    String path, {
    T Function(Map<String, dynamic>)? fromJson,
  }) async {
    final uri = Uri.parse('$_baseUrl$path');
    try {
      final response = await _client
          .delete(uri, headers: _headers)
          .timeout(AppConstants.readTimeout);
      return _handleResponse(response, fromJson: fromJson);
    } on TimeoutException {
      throw ApiException('Request timeout');
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException('Network error: $e');
    }
  }

  // SSE streaming for chat
  Stream<SseEvent> streamChat({
    required String message,
    String? sessionId,
    bool voice = false,
  }) {
    return SseClient.connect(
      url: '$_baseUrl/api/chat',
      headers: _headers,
      body: jsonEncode({
        'message': message,
        if (sessionId != null) 'session_id': sessionId,
        'voice': voice,
      }),
    );
  }

  // Specific API endpoints

  Future<Map<String, dynamic>> checkStatus() async {
    return get('/api/status');
  }

  Future<Map<String, dynamic>> checkEngineHealth() async {
    return get('/api/engine/health');
  }

  Future<bool> testConnection() async {
    try {
      await checkStatus();
      return true;
    } catch (_) {
      return false;
    }
  }

  // Sessions
  Future<List<dynamic>> getSessions() async {
    final result = await get('/api/chat/sessions');
    return result['sessions'] as List<dynamic>? ?? result['data'] as List<dynamic>? ?? [];
  }

  Future<List<dynamic>> getSessionMessages(String sessionId) async {
    final result = await get('/api/chat/sessions/$sessionId/messages');
    return result['messages'] as List<dynamic>? ?? result['data'] as List<dynamic>? ?? [];
  }

  Future<List<dynamic>> searchSessions(String query) async {
    final result = await post('/api/chat/search', body: {'query': query});
    return result['sessions'] as List<dynamic>? ?? result['data'] as List<dynamic>? ?? [];
  }

  Future<void> deleteSession(String sessionId) async {
    await delete('/api/chat/sessions/$sessionId');
  }

  // Knowledge
  Future<List<dynamic>> getCollections() async {
    final result = await get('/api/knowledge/collections');
    return result['collections'] as List<dynamic>? ?? result['data'] as List<dynamic>? ?? [];
  }

  Future<List<dynamic>> searchKnowledge(String query, {String? collection}) async {
    final result = await post('/api/knowledge/search', body: {
      'query': query,
      if (collection != null) 'collection': collection,
    });
    return result['results'] as List<dynamic>? ?? result['data'] as List<dynamic>? ?? [];
  }

  // Memory
  Future<Map<String, dynamic>> getMemoryStats() async {
    return get('/api/memory/stats');
  }

  Future<List<dynamic>> searchMemory(String query) async {
    final result = await post('/api/memory/search', body: {'query': query});
    return result['memories'] as List<dynamic>? ?? result['results'] as List<dynamic>? ?? [];
  }

  Future<void> storeMemory({
    required String content,
    String? category,
    Map<String, dynamic>? metadata,
  }) async {
    await post('/api/memory/store', body: {
      'content': content,
      if (category != null) 'category': category,
      if (metadata != null) 'metadata': metadata,
    });
  }

  // Tools
  Future<List<dynamic>> getAvailableTools() async {
    final result = await get('/api/tools/available');
    return result['tools'] as List<dynamic>? ?? result['data'] as List<dynamic>? ?? [];
  }

  // Skills
  Future<List<dynamic>> getSkills() async {
    final result = await get('/api/skills');
    return result['skills'] as List<dynamic>? ?? result['data'] as List<dynamic>? ?? [];
  }

  // Models
  Future<List<dynamic>> getModels() async {
    final result = await post('/api/ollama/models', body: {});
    return result['models'] as List<dynamic>? ?? result['data'] as List<dynamic>? ?? [];
  }

  // Subagents
  Future<List<dynamic>> getSubagents() async {
    final result = await get('/api/subagents');
    return result['subagents'] as List<dynamic>? ?? result['data'] as List<dynamic>? ?? [];
  }

  // MCP Tools
  Future<List<dynamic>> getMcpTools() async {
    final result = await get('/api/mcp/tools');
    return result['tools'] as List<dynamic>? ?? result['data'] as List<dynamic>? ?? [];
  }

  // Voice
  Future<String> transcribeAudio(String audioPath) async {
    final uri = Uri.parse('$_baseUrl/api/voice/transcribe');
    final request = http.MultipartRequest('POST', uri)
      ..headers.addAll(_headers)
      ..files.add(await http.MultipartFile.fromPath('audio', audioPath));
    final response = await request.send();
    final body = await response.stream.bytesToString();
    if (response.statusCode == 200) {
      final json = jsonDecode(body) as Map<String, dynamic>;
      return json['text'] as String? ?? '';
    }
    throw ApiException('Transcription failed', statusCode: response.statusCode);
  }

  Future<List<int>> synthesizeSpeech(String text) async {
    final uri = Uri.parse('$_baseUrl/api/voice/synthesize');
    final response = await _client.post(
      uri,
      headers: _headers,
      body: jsonEncode({'text': text}),
    );
    if (response.statusCode == 200) {
      return response.bodyBytes;
    }
    throw ApiException('Speech synthesis failed', statusCode: response.statusCode);
  }
}
