// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'memory.dart';

MemoryEntry _$MemoryEntryFromJson(Map<String, dynamic> json) => MemoryEntry(
      id: json['id'] as String,
      content: json['content'] as String,
      category: json['category'] as String?,
      createdAt: DateTime.parse(json['createdAt'] as String),
      updatedAt: json['updatedAt'] != null
          ? DateTime.parse(json['updatedAt'] as String)
          : null,
      relevanceScore: (json['relevanceScore'] as num?)?.toDouble(),
      metadata: json['metadata'] as Map<String, dynamic>?,
    );

Map<String, dynamic> _$MemoryEntryToJson(MemoryEntry instance) =>
    <String, dynamic>{
      'id': instance.id,
      'content': instance.content,
      'category': instance.category,
      'createdAt': instance.createdAt.toIso8601String(),
      'updatedAt': instance.updatedAt?.toIso8601String(),
      'relevanceScore': instance.relevanceScore,
      'metadata': instance.metadata,
    };

MemoryStats _$MemoryStatsFromJson(Map<String, dynamic> json) => MemoryStats(
      totalMemories: json['totalMemories'] as int,
      totalCategories: json['totalCategories'] as int,
      categoryBreakdown: (json['categoryBreakdown'] as Map<String, dynamic>?)
          ?.map((k, v) => MapEntry(k, v as int)),
      lastUpdated: json['lastUpdated'] != null
          ? DateTime.parse(json['lastUpdated'] as String)
          : null,
    );

Map<String, dynamic> _$MemoryStatsToJson(MemoryStats instance) =>
    <String, dynamic>{
      'totalMemories': instance.totalMemories,
      'totalCategories': instance.totalCategories,
      'categoryBreakdown': instance.categoryBreakdown,
      'lastUpdated': instance.lastUpdated?.toIso8601String(),
    };
