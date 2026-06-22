import 'dart:async';
import 'dart:convert';
import 'dart:io';

class SseEvent {
  final String? event;
  final String? data;
  final String? id;

  SseEvent({this.event, this.data, this.id});

  Map<String, dynamic>? get jsonData {
    if (data == null) return null;
    try {
      return jsonDecode(data!) as Map<String, dynamic>;
    } catch (_) {
      return null;
    }
  }

  @override
  String toString() => 'SseEvent(event: $event, data: $data, id: $id)';
}

class SseClient {
  SseClient._();

  static Stream<SseEvent> connect({
    required String url,
    required Map<String, String> headers,
    String? body,
    String method = 'POST',
  }) async* {
    HttpClient? httpClient;
    HttpClientRequest? request;

    try {
      httpClient = HttpClient();
      final uri = Uri.parse(url);
      request = await httpClient.openUrl(method, uri);

      // Set headers
      request.headers.set('Accept', 'text/event-stream');
      request.headers.set('Cache-Control', 'no-cache');
      request.headers.set('Connection', 'keep-alive');
      headers.forEach((key, value) {
        request!.headers.set(key, value);
      });

      // Write body if present
      if (body != null) {
        request.write(body);
      }

      final response = await request.close();

      if (response.statusCode != 200) {
        final responseBody = await response.transform(utf8.decoder).join();
        throw Exception('SSE connection failed: ${response.statusCode} - $responseBody');
      }

      String buffer = '';
      String? currentEvent;
      String? currentId;

      await for (final chunk in response.transform(utf8.decoder)) {
        buffer += chunk;
        final lines = buffer.split('\n');
        buffer = lines.removeLast(); // Keep incomplete line in buffer

        for (final line in lines) {
          if (line.isEmpty) {
            // Empty line signals end of event
            if (currentEvent != null || buffer.isNotEmpty) {
              // Event already yielded when data line found
            }
            currentEvent = null;
            continue;
          }

          if (line.startsWith('event:')) {
            currentEvent = line.substring(6).trim();
          } else if (line.startsWith('data:')) {
            final data = line.substring(5).trim();
            yield SseEvent(
              event: currentEvent,
              data: data,
              id: currentId,
            );
          } else if (line.startsWith('id:')) {
            currentId = line.substring(3).trim();
          } else if (line.startsWith('retry:')) {
            // Ignore retry directive for now
          } else if (!line.startsWith(':')) {
            // Treat as data without prefix (some servers do this)
            yield SseEvent(
              event: currentEvent,
              data: line,
              id: currentId,
            );
          }
        }
      }
    } catch (e) {
      if (e is Exception) {
        rethrow;
      }
      throw Exception('SSE connection error: $e');
    } finally {
      httpClient?.close();
    }
  }

  /// Parse SSE data that comes as JSON with token/complete/error types
  static Stream<ChatStreamEvent> parseChatStream(Stream<SseEvent> sseStream) async* {
    await for (final event in sseStream) {
      final json = event.jsonData;
      if (json == null) continue;

      final type = json['type'] as String? ?? 'token';
      switch (type) {
        case 'token':
          final token = json['token'] as String? ?? json['content'] as String? ?? '';
          yield ChatStreamEvent.token(token);
          break;
        case 'complete':
          yield ChatStreamEvent.complete(json['message'] as Map<String, dynamic>?);
          break;
        case 'error':
          yield ChatStreamEvent.error(json['error'] as String? ?? 'Unknown error');
          break;
        case 'tool_call':
          yield ChatStreamEvent.toolCall(json['tool'] as String? ?? '', json['args'] as Map<String, dynamic>? ?? {});
          break;
        case 'tool_result':
          yield ChatStreamEvent.toolResult(json['tool'] as String? ?? '', json['result']);
          break;
        default:
          // Try to extract token from any data
          final token = json['token'] as String? ?? json['content'] as String?;
          if (token != null) {
            yield ChatStreamEvent.token(token);
          }
      }
    }
  }
}

class ChatStreamEvent {
  final String type;
  final String? token;
  final Map<String, dynamic>? message;
  final String? error;
  final String? toolName;
  final Map<String, dynamic>? toolArgs;
  final dynamic toolResult;

  const ChatStreamEvent._({
    required this.type,
    this.token,
    this.message,
    this.error,
    this.toolName,
    this.toolArgs,
    this.toolResult,
  });

  factory ChatStreamEvent.token(String token) =>
      ChatStreamEvent._(type: 'token', token: token);

  factory ChatStreamEvent.complete(Map<String, dynamic>? message) =>
      ChatStreamEvent._(type: 'complete', message: message);

  factory ChatStreamEvent.error(String error) =>
      ChatStreamEvent._(type: 'error', error: error);

  factory ChatStreamEvent.toolCall(String name, Map<String, dynamic> args) =>
      ChatStreamEvent._(type: 'tool_call', toolName: name, toolArgs: args);

  factory ChatStreamEvent.toolResult(String name, dynamic result) =>
      ChatStreamEvent._(type: 'tool_result', toolName: name, toolResult: result);
}
