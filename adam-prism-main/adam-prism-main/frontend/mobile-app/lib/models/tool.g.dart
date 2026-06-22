// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'tool.dart';

AgentTool _$AgentToolFromJson(Map<String, dynamic> json) => AgentTool(
      id: json['id'] as String,
      name: json['name'] as String,
      description: json['description'] as String?,
      category: json['category'] as String?,
      isEnabled: json['isEnabled'] as bool,
      parameters: json['parameters'] as Map<String, dynamic>?,
      status: json['status'] as String?,
    );

Map<String, dynamic> _$AgentToolToJson(AgentTool instance) => <String, dynamic>{
      'id': instance.id,
      'name': instance.name,
      'description': instance.description,
      'category': instance.category,
      'isEnabled': instance.isEnabled,
      'parameters': instance.parameters,
      'status': instance.status,
    };

McpTool _$McpToolFromJson(Map<String, dynamic> json) => McpTool(
      name: json['name'] as String,
      description: json['description'] as String?,
      inputSchema: json['inputSchema'] as Map<String, dynamic>?,
      server: json['server'] as String?,
    );

Map<String, dynamic> _$McpToolToJson(McpTool instance) => <String, dynamic>{
      'name': instance.name,
      'description': instance.description,
      'inputSchema': instance.inputSchema,
      'server': instance.server,
    };
