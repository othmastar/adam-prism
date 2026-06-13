// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'chat_message.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

ChatMessage _$ChatMessageFromJson(Map<String, dynamic> json) => ChatMessage(
      id: json['id'] as String,
      sessionId: json['sessionId'] as String,
      role: $enumDecode(_$MessageRoleEnumMap, json['role']),
      content: json['content'] as String,
      status: $enumDecode(_$MessageStatusEnumMap, json['status']),
      timestamp: DateTime.parse(json['timestamp'] as String),
      model: json['model'] as String?,
      metadata: json['metadata'] as Map<String, dynamic>?,
      toolCalls: (json['toolCalls'] as List<dynamic>?)
          ?.map((e) => ToolCall.fromJson(e as Map<String, dynamic>))
          .toList(),
      responseTime: json['responseTime'] != null
          ? Duration(microseconds: json['responseTime'] as int)
          : null,
      tokenCount: json['tokenCount'] as int?,
    );

Map<String, dynamic> _$ChatMessageToJson(ChatMessage instance) =>
    <String, dynamic>{
      'id': instance.id,
      'sessionId': instance.sessionId,
      'role': _$MessageRoleEnumMap[instance.role]!,
      'content': instance.content,
      'status': _$MessageStatusEnumMap[instance.status]!,
      'timestamp': instance.timestamp.toIso8601String(),
      'model': instance.model,
      'metadata': instance.metadata,
      'toolCalls': instance.toolCalls?.map((e) => e.toJson()).toList(),
      'responseTime': instance.responseTime?.inMicroseconds,
      'tokenCount': instance.tokenCount,
    };

const _$MessageRoleEnumMap = {
  MessageRole.user: 'user',
  MessageRole.assistant: 'assistant',
  MessageRole.system: 'system',
  MessageRole.tool: 'tool',
};

const _$MessageStatusEnumMap = {
  MessageStatus.sending: 'sending',
  MessageStatus.sent: 'sent',
  MessageStatus.streaming: 'streaming',
  MessageStatus.error: 'error',
  MessageStatus.complete: 'complete',
};

ToolCall _$ToolCallFromJson(Map<String, dynamic> json) => ToolCall(
      id: json['id'] as String,
      name: json['name'] as String,
      arguments: json['arguments'] as Map<String, dynamic>,
      result: json['result'],
      status: $enumDecode(_$ToolCallStatusEnumMap, json['status']),
    );

Map<String, dynamic> _$ToolCallToJson(ToolCall instance) => <String, dynamic>{
      'id': instance.id,
      'name': instance.name,
      'arguments': instance.arguments,
      'result': instance.result,
      'status': _$ToolCallStatusEnumMap[instance.status]!,
    };

const _$ToolCallStatusEnumMap = {
  ToolCallStatus.pending: 'pending',
  ToolCallStatus.running: 'running',
  ToolCallStatus.completed: 'completed',
  ToolCallStatus.failed: 'failed',
};

T $enumDecode<T>(Map<T, String> enumMap, dynamic source) {
  if (source is! String) {
    throw ArgumentError('`$source` is not a valid enum value');
  }
  for (final entry in enumMap.entries) {
    if (entry.value == source) return entry.key;
  }
  throw ArgumentError('`$source` is not a valid enum value');
}
