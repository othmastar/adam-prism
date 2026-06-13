// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'knowledge.dart';

KnowledgeCollection _$KnowledgeCollectionFromJson(Map<String, dynamic> json) =>
    KnowledgeCollection(
      id: json['id'] as String,
      name: json['name'] as String,
      description: json['description'] as String?,
      documentCount: json['documentCount'] as int,
      createdAt: DateTime.parse(json['createdAt'] as String),
      updatedAt: json['updatedAt'] != null
          ? DateTime.parse(json['updatedAt'] as String)
          : null,
      metadata: json['metadata'] as Map<String, dynamic>?,
    );

Map<String, dynamic> _$KnowledgeCollectionToJson(KnowledgeCollection instance) =>
    <String, dynamic>{
      'id': instance.id,
      'name': instance.name,
      'description': instance.description,
      'documentCount': instance.documentCount,
      'createdAt': instance.createdAt.toIso8601String(),
      'updatedAt': instance.updatedAt?.toIso8601String(),
      'metadata': instance.metadata,
    };

KnowledgeSearchResult _$KnowledgeSearchResultFromJson(Map<String, dynamic> json) =>
    KnowledgeSearchResult(
      id: json['id'] as String,
      content: json['content'] as String,
      collection: json['collection'] as String,
      score: (json['score'] as num).toDouble(),
      metadata: json['metadata'] as Map<String, dynamic>?,
    );

Map<String, dynamic> _$KnowledgeSearchResultToJson(KnowledgeSearchResult instance) =>
    <String, dynamic>{
      'id': instance.id,
      'content': instance.content,
      'collection': instance.collection,
      'score': instance.score,
      'metadata': instance.metadata,
    };
