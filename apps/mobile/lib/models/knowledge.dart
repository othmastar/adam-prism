import 'package:json_annotation/json_annotation.dart';

part 'knowledge.g.dart';

@JsonSerializable()
class KnowledgeCollection {
  final String id;
  final String name;
  final String? description;
  final int documentCount;
  final DateTime createdAt;
  final DateTime? updatedAt;
  final Map<String, dynamic>? metadata;

  KnowledgeCollection({
    required this.id,
    required this.name,
    this.description,
    this.documentCount = 0,
    required this.createdAt,
    this.updatedAt,
    this.metadata,
  });

  factory KnowledgeCollection.fromJson(Map<String, dynamic> json) =>
      _$KnowledgeCollectionFromJson(json);

  Map<String, dynamic> toJson() => _$KnowledgeCollectionToJson(this);

  static KnowledgeCollection fromApi(Map<String, dynamic> json) {
    return KnowledgeCollection(
      id: json['id'] as String? ?? json['name'] as String? ?? '',
      name: json['name'] as String? ?? '',
      description: json['description'] as String?,
      documentCount: json['document_count'] as int? ?? json['count'] as int? ?? 0,
      createdAt: json['created_at'] != null
          ? DateTime.parse(json['created_at'] as String)
          : DateTime.now(),
      updatedAt: json['updated_at'] != null
          ? DateTime.parse(json['updated_at'] as String)
          : null,
      metadata: json['metadata'] as Map<String, dynamic>?,
    );
  }
}

@JsonSerializable()
class KnowledgeSearchResult {
  final String id;
  final String content;
  final String collection;
  final double score;
  final Map<String, dynamic>? metadata;

  KnowledgeSearchResult({
    required this.id,
    required this.content,
    required this.collection,
    required this.score,
    this.metadata,
  });

  factory KnowledgeSearchResult.fromJson(Map<String, dynamic> json) =>
      _$KnowledgeSearchResultFromJson(json);

  Map<String, dynamic> toJson() => _$KnowledgeSearchResultToJson(this);

  static KnowledgeSearchResult fromApi(Map<String, dynamic> json) {
    return KnowledgeSearchResult(
      id: json['id'] as String? ?? '',
      content: json['content'] as String? ?? json['text'] as String? ?? '',
      collection: json['collection'] as String? ?? json['source'] as String? ?? '',
      score: (json['score'] as num?)?.toDouble() ?? 0.0,
      metadata: json['metadata'] as Map<String, dynamic>?,
    );
  }
}
