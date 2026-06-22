import 'package:json_annotation/json_annotation.dart';

part 'skill.g.dart';

@JsonSerializable()
class Skill {
  final String id;
  final String name;
  final String? description;
  final String? category;
  final bool isEnabled;
  final String? version;
  final Map<String, dynamic>? config;
  final String? status;

  Skill({
    required this.id,
    required this.name,
    this.description,
    this.category,
    this.isEnabled = true,
    this.version,
    this.config,
    this.status,
  });

  factory Skill.fromJson(Map<String, dynamic> json) =>
      _$SkillFromJson(json);

  Map<String, dynamic> toJson() => _$SkillToJson(this);

  static Skill fromApi(Map<String, dynamic> json) {
    return Skill(
      id: json['id'] as String? ?? json['name'] as String? ?? '',
      name: json['name'] as String? ?? '',
      description: json['description'] as String?,
      category: json['category'] as String? ?? json['type'] as String?,
      isEnabled: json['enabled'] as bool? ?? json['is_enabled'] as bool? ?? true,
      version: json['version'] as String?,
      config: json['config'] as Map<String, dynamic>?,
      status: json['status'] as String?,
    );
  }
}

@JsonSerializable()
class Subagent {
  final String id;
  final String name;
  final String? description;
  final String? model;
  final String status;
  final String? role;
  final Map<String, dynamic>? capabilities;
  final DateTime? lastActive;

  Subagent({
    required this.id,
    required this.name,
    this.description,
    this.model,
    this.status = 'idle',
    this.role,
    this.capabilities,
    this.lastActive,
  });

  factory Subagent.fromJson(Map<String, dynamic> json) =>
      _$SubagentFromJson(json);

  Map<String, dynamic> toJson() => _$SubagentToJson(this);

  static Subagent fromApi(Map<String, dynamic> json) {
    return Subagent(
      id: json['id'] as String? ?? json['name'] as String? ?? '',
      name: json['name'] as String? ?? '',
      description: json['description'] as String?,
      model: json['model'] as String?,
      status: json['status'] as String? ?? 'idle',
      role: json['role'] as String?,
      capabilities: json['capabilities'] as Map<String, dynamic>?,
      lastActive: json['last_active'] != null
          ? DateTime.parse(json['last_active'] as String)
          : null,
    );
  }
}
