import 'package:json_annotation/json_annotation.dart';

part 'memory.g.dart';

@JsonSerializable()
class MemoryEntry {
  final String id;
  final String content;
  final String? category;
  final DateTime createdAt;
  final DateTime? updatedAt;
  final double? relevanceScore;
  final Map<String, dynamic>? metadata;

  MemoryEntry({
    required this.id,
    required this.content,
    this.category,
    required this.createdAt,
    this.updatedAt,
    this.relevanceScore,
    this.metadata,
  });

  MemoryEntry copyWith({
    String? id,
    String? content,
    String? category,
    DateTime? createdAt,
    DateTime? updatedAt,
    double? relevanceScore,
    Map<String, dynamic>? metadata,
  }) {
    return MemoryEntry(
      id: id ?? this.id,
      content: content ?? this.content,
      category: category ?? this.category,
      createdAt: createdAt ?? this.createdAt,
      updatedAt: updatedAt ?? this.updatedAt,
      relevanceScore: relevanceScore ?? this.relevanceScore,
      metadata: metadata ?? this.metadata,
    );
  }

  factory MemoryEntry.fromJson(Map<String, dynamic> json) =>
      _$MemoryEntryFromJson(json);

  Map<String, dynamic> toJson() => _$MemoryEntryToJson(this);

  static MemoryEntry fromApi(Map<String, dynamic> json) {
    return MemoryEntry(
      id: json['id'] as String? ?? '',
      content: json['content'] as String? ?? json['text'] as String? ?? '',
      category: json['category'] as String? ?? json['type'] as String?,
      createdAt: json['created_at'] != null
          ? DateTime.parse(json['created_at'] as String)
          : DateTime.now(),
      updatedAt: json['updated_at'] != null
          ? DateTime.parse(json['updated_at'] as String)
          : null,
      relevanceScore: (json['score'] as num?)?.toDouble() ??
          (json['relevance'] as num?)?.toDouble(),
      metadata: json['metadata'] as Map<String, dynamic>?,
    );
  }
}

@JsonSerializable()
class MemoryStats {
  final int totalMemories;
  final int totalCategories;
  final Map<String, int>? categoryBreakdown;
  final DateTime? lastUpdated;

  MemoryStats({
    this.totalMemories = 0,
    this.totalCategories = 0,
    this.categoryBreakdown,
    this.lastUpdated,
  });

  factory MemoryStats.fromJson(Map<String, dynamic> json) =>
      _$MemoryStatsFromJson(json);

  Map<String, dynamic> toJson() => _$MemoryStatsToJson(this);

  static MemoryStats fromApi(Map<String, dynamic> json) {
    return MemoryStats(
      totalMemories: json['total'] as int? ?? json['count'] as int? ?? 0,
      totalCategories: json['categories'] as int? ?? 0,
      categoryBreakdown: (json['breakdown'] as Map<String, dynamic>?)?.map(
        (k, v) => MapEntry(k, v as int),
      ),
      lastUpdated: json['last_updated'] != null
          ? DateTime.parse(json['last_updated'] as String)
          : null,
    );
  }
}
