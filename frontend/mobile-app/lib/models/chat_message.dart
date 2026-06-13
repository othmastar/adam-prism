import 'package:json_annotation/json_annotation.dart';

part 'chat_message.g.dart';

enum MessageRole { user, assistant, system, tool }

enum MessageStatus { sending, sent, streaming, error, complete }

@JsonSerializable()
class ChatMessage {
  final String id;
  final String sessionId;
  final MessageRole role;
  final String content;
  final MessageStatus status;
  final DateTime timestamp;
  final String? model;
  final Map<String, dynamic>? metadata;
  final List<ToolCall>? toolCalls;
  final Duration? responseTime;
  final int? tokenCount;

  ChatMessage({
    required this.id,
    required this.sessionId,
    required this.role,
    required this.content,
    this.status = MessageStatus.sent,
    required this.timestamp,
    this.model,
    this.metadata,
    this.toolCalls,
    this.responseTime,
    this.tokenCount,
  });

  ChatMessage copyWith({
    String? id,
    String? sessionId,
    MessageRole? role,
    String? content,
    MessageStatus? status,
    DateTime? timestamp,
    String? model,
    Map<String, dynamic>? metadata,
    List<ToolCall>? toolCalls,
    Duration? responseTime,
    int? tokenCount,
  }) {
    return ChatMessage(
      id: id ?? this.id,
      sessionId: sessionId ?? this.sessionId,
      role: role ?? this.role,
      content: content ?? this.content,
      status: status ?? this.status,
      timestamp: timestamp ?? this.timestamp,
      model: model ?? this.model,
      metadata: metadata ?? this.metadata,
      toolCalls: toolCalls ?? this.toolCalls,
      responseTime: responseTime ?? this.responseTime,
      tokenCount: tokenCount ?? this.tokenCount,
    );
  }

  factory ChatMessage.fromJson(Map<String, dynamic> json) =>
      _$ChatMessageFromJson(json);

  Map<String, dynamic> toJson() => _$ChatMessageToJson(this);

  static MessageRole _parseRole(String? role) {
    switch (role?.toLowerCase()) {
      case 'user':
        return MessageRole.user;
      case 'assistant':
        return MessageRole.assistant;
      case 'system':
        return MessageRole.system;
      case 'tool':
        return MessageRole.tool;
      default:
        return MessageRole.assistant;
    }
  }
}

@JsonSerializable()
class ToolCall {
  final String id;
  final String name;
  final Map<String, dynamic> arguments;
  final dynamic result;
  final ToolCallStatus status;

  ToolCall({
    required this.id,
    required this.name,
    required this.arguments,
    this.result,
    this.status = ToolCallStatus.pending,
  });

  ToolCall copyWith({
    String? id,
    String? name,
    Map<String, dynamic>? arguments,
    dynamic result,
    ToolCallStatus? status,
  }) {
    return ToolCall(
      id: id ?? this.id,
      name: name ?? this.name,
      arguments: arguments ?? this.arguments,
      result: result ?? this.result,
      status: status ?? this.status,
    );
  }

  factory ToolCall.fromJson(Map<String, dynamic> json) =>
      _$ToolCallFromJson(json);

  Map<String, dynamic> toJson() => _$ToolCallToJson(this);
}

enum ToolCallStatus { pending, running, completed, failed }
