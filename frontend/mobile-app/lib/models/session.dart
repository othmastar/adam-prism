import 'package:json_annotation/json_annotation.dart';

part 'session.g.dart';

@JsonSerializable()
class Session {
  final String id;
  final String title;
  final DateTime createdAt;
  final DateTime updatedAt;
  final int messageCount;
  final String? model;
  final String? preview;
  final bool isPinned;
  final Map<String, dynamic>? metadata;

  Session({
    required this.id,
    required this.title,
    required this.createdAt,
    required this.updatedAt,
    this.messageCount = 0,
    this.model,
    this.preview,
    this.isPinned = false,
    this.metadata,
  });

  Session copyWith({
    String? id,
    String? title,
    DateTime? createdAt,
    DateTime? updatedAt,
    int? messageCount,
    String? model,
    String? preview,
    bool? isPinned,
    Map<String, dynamic>? metadata,
  }) {
    return Session(
      id: id ?? this.id,
      title: title ?? this.title,
      createdAt: createdAt ?? this.createdAt,
      updatedAt: updatedAt ?? this.updatedAt,
      messageCount: messageCount ?? this.messageCount,
      model: model ?? this.model,
      preview: preview ?? this.preview,
      isPinned: isPinned ?? this.isPinned,
      metadata: metadata ?? this.metadata,
    );
  }

  factory Session.fromJson(Map<String, dynamic> json) =>
      _$SessionFromJson(json);

  Map<String, dynamic> toJson() => _$SessionToJson(this);

  static Session fromApi(Map<String, dynamic> json) {
    return Session(
      id: json['id'] as String? ?? '',
      title: json['title'] as String? ?? 'محادثة جديدة',
      createdAt: json['created_at'] != null
          ? DateTime.parse(json['created_at'] as String)
          : DateTime.now(),
      updatedAt: json['updated_at'] != null
          ? DateTime.parse(json['updated_at'] as String)
          : DateTime.now(),
      messageCount: json['message_count'] as int? ?? 0,
      model: json['model'] as String?,
      preview: json['preview'] as String? ?? json['last_message'] as String?,
      isPinned: json['is_pinned'] as bool? ?? false,
      metadata: json['metadata'] as Map<String, dynamic>?,
    );
  }
}
