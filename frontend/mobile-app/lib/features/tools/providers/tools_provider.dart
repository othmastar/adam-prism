import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/api/api_client.dart';
import '../../../models/tool.dart';
import '../../../models/skill.dart';

class ToolsState {
  final List<AgentTool> tools;
  final List<Skill> skills;
  final List<Subagent> subagents;
  final List<McpTool> mcpTools;
  final bool isLoading;
  final String? error;
  final int selectedTab;

  const ToolsState({
    this.tools = const [],
    this.skills = const [],
    this.subagents = const [],
    this.mcpTools = const [],
    this.isLoading = false,
    this.error,
    this.selectedTab = 0,
  });

  ToolsState copyWith({
    List<AgentTool>? tools,
    List<Skill>? skills,
    List<Subagent>? subagents,
    List<McpTool>? mcpTools,
    bool? isLoading,
    String? error,
    int? selectedTab,
  }) {
    return ToolsState(
      tools: tools ?? this.tools,
      skills: skills ?? this.skills,
      subagents: subagents ?? this.subagents,
      mcpTools: mcpTools ?? this.mcpTools,
      isLoading: isLoading ?? this.isLoading,
      error: error,
      selectedTab: selectedTab ?? this.selectedTab,
    );
  }
}

class ToolsNotifier extends StateNotifier<ToolsState> {
  ToolsNotifier() : super(const ToolsState());

  Future<void> loadAll() async {
    state = state.copyWith(isLoading: true);
    try {
      final results = await Future.wait([
        ApiClient.instance.getAvailableTools(),
        ApiClient.instance.getSkills(),
        ApiClient.instance.getSubagents(),
        ApiClient.instance.getMcpTools(),
      ]);

      state = state.copyWith(
        tools: (results[0] as List).map((t) => AgentTool.fromApi(t as Map<String, dynamic>)).toList(),
        skills: (results[1] as List).map((s) => Skill.fromApi(s as Map<String, dynamic>)).toList(),
        subagents: (results[2] as List).map((a) => Subagent.fromApi(a as Map<String, dynamic>)).toList(),
        mcpTools: (results[3] as List).map((t) => McpTool.fromApi(t as Map<String, dynamic>)).toList(),
        isLoading: false,
      );
    } catch (e) {
      state = state.copyWith(isLoading: false, error: e.toString());
    }
  }

  void setTab(int index) {
    state = state.copyWith(selectedTab: index);
  }
}

final toolsProvider = StateNotifierProvider<ToolsNotifier, ToolsState>(
  (ref) => ToolsNotifier(),
);
