// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'skill.dart';

Skill _$SkillFromJson(Map<String, dynamic> json) => Skill(
      id: json['id'] as String,
      name: json['name'] as String,
      description: json['description'] as String?,
      category: json['category'] as String?,
      isEnabled: json['isEnabled'] as bool,
      version: json['version'] as String?,
      config: json['config'] as Map<String, dynamic>?,
      status: json['status'] as String?,
    );

Map<String, dynamic> _$SkillToJson(Skill instance) => <String, dynamic>{
      'id': instance.id,
      'name': instance.name,
      'description': instance.description,
      'category': instance.category,
      'isEnabled': instance.isEnabled,
      'version': instance.version,
      'config': instance.config,
      'status': instance.status,
    };

Subagent _$SubagentFromJson(Map<String, dynamic> json) => Subagent(
      id: json['id'] as String,
      name: json['name'] as String,
      description: json['description'] as String?,
      model: json['model'] as String?,
      status: json['status'] as String,
      role: json['role'] as String?,
      capabilities: json['capabilities'] as Map<String, dynamic>?,
      lastActive: json['lastActive'] != null
          ? DateTime.parse(json['lastActive'] as String)
          : null,
    );

Map<String, dynamic> _$SubagentToJson(Subagent instance) => <String, dynamic>{
      'id': instance.id,
      'name': instance.name,
      'description': instance.description,
      'model': instance.model,
      'status': instance.status,
      'role': instance.role,
      'capabilities': instance.capabilities,
      'lastActive': instance.lastActive?.toIso8601String(),
    };
