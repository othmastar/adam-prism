// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'session.dart';

Session _$SessionFromJson(Map<String, dynamic> json) => Session(
      id: json['id'] as String,
      title: json['title'] as String,
      createdAt: DateTime.parse(json['createdAt'] as String),
      updatedAt: DateTime.parse(json['updatedAt'] as String),
      messageCount: json['messageCount'] as int,
      model: json['model'] as String?,
      preview: json['preview'] as String?,
      isPinned: json['isPinned'] as bool,
      metadata: json['metadata'] as Map<String, dynamic>?,
    );

Map<String, dynamic> _$SessionToJson(Session instance) => <String, dynamic>{
      'id': instance.id,
      'title': instance.title,
      'createdAt': instance.createdAt.toIso8601String(),
      'updatedAt': instance.updatedAt.toIso8601String(),
      'messageCount': instance.messageCount,
      'model': instance.model,
      'preview': instance.preview,
      'isPinned': instance.isPinned,
      'metadata': instance.metadata,
    };
