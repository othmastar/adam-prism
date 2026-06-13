import 'package:json_annotation/json_annotation.dart';

part 'tool.g.dart';

@JsonSerializable()
class AgentTool {
  final String id;
  final String name;
  final String? description;
  final String? category;
  final bool isEnabled;
  final Map<String, dynamic>? parameters;
  final String? status;

  AgentTool({
    required this.id,
    required this.name,
    this.description,
    this.category,
    this.isEnabled = true,
    this.parameters,
    this.status,
  });

  factory AgentTool.fromJson(Map<String, dynamic> json) =>
      _$AgentToolFromJson(json);

  Map<String, dynamic> toJson() => _$AgentToolToJson(this);

  static AgentTool fromApi(Map<String, dynamic> json) {
    return AgentTool(
      id: json['id'] as String? ?? json['name'] as String? ?? '',
      name: json['name'] as String? ?? '',
      description: json['description'] as String?,
      category: json['category'] as String? ?? json['type'] as String?,
      isEnabled: json['enabled'] as bool? ?? json['is_enabled'] as bool? ?? true,
      parameters: json['parameters'] as Map<String, dynamic>? ?? json['schema'] as Map<String, dynamic>?,
      status: json['status'] as String?,
    );
  }
}

@JsonSerializable()
class McpTool {
  final String name;
  final String? description;
  final Map<String, dynamic>? inputSchema;
  final String? server;

  McpTool({
    required this.name,
    this.description,
    this.inputSchema,
    this.server,
  });

  factory McpTool.fromJson(Map<String, dynamic> json) =>
      _$McpToolFromJson(json);

  Map<String, dynamic> toJson() => _$McpToolToJson(this);

  static McpTool fromApi(Map<String, dynamic> json) {
    return McpTool(
      name: json['name'] as String? ?? '',
      description: json['description'] as String?,
      inputSchema: json['inputSchema'] as Map<String, dynamic>? ?? json['input_schema'] as Map<String, dynamic>?,
      server: json['server'] as String?,
    );
  }
}
