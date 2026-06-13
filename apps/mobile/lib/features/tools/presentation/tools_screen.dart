import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/theme/app_theme.dart';
import '../../../core/utils/helpers.dart';
import '../../../models/tool.dart';
import '../../../models/skill.dart';
import '../providers/tools_provider.dart';

class ToolsScreen extends ConsumerStatefulWidget {
  const ToolsScreen({super.key});

  @override
  ConsumerState<ToolsScreen> createState() => _ToolsScreenState();
}

class _ToolsScreenState extends ConsumerState<ToolsScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 4, vsync: this);
    _tabController.addListener(() {
      ref.read(toolsProvider.notifier).setTab(_tabController.index);
    });
    WidgetsBinding.instance.addPostFrameCallback((_) {
      ref.read(toolsProvider.notifier).loadAll();
    });
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(toolsProvider);

    return Container(
      decoration: const BoxDecoration(color: Color(0xFF0F0F1A)),
      child: Column(
        children: [
          // Header
          Container(
            decoration: const BoxDecoration(
              color: Color(0xFF1A1A2E),
              border: Border(
                bottom: BorderSide(color: Color(0xFF2A2A45), width: 0.5),
              ),
            ),
            child: SafeArea(
              bottom: false,
              child: Column(
                children: [
                  Padding(
                    padding: const EdgeInsets.fromLTRB(20, 16, 20, 0),
                    child: Row(
                      children: [
                        const Text(
                          'الأدوات والمهارات',
                          style: TextStyle(
                            color: Colors.white,
                            fontSize: 24,
                            fontWeight: FontWeight.w800,
                          ),
                        ),
                        const Spacer(),
                        IconButton(
                          icon: const Icon(Icons.refresh, color: Color(0xFF6B6B8D)),
                          onPressed: () => ref.read(toolsProvider.notifier).loadAll(),
                        ),
                      ],
                    ),
                  ),
                  TabBar(
                    controller: _tabController,
                    isScrollable: true,
                    labelColor: const Color(0xFF6C63FF),
                    unselectedLabelColor: const Color(0xFF6B6B8D),
                    indicatorColor: const Color(0xFF6C63FF),
                    indicatorSize: TabBarIndicatorSize.label,
                    labelStyle: const TextStyle(fontWeight: FontWeight.w600, fontSize: 14),
                    tabs: [
                      Tab(text: 'الأدوات (${state.tools.length})'),
                      Tab(text: 'المهارات (${state.skills.length})'),
                      Tab(text: 'الوكلاء (${state.subagents.length})'),
                      Tab(text: 'MCP (${state.mcpTools.length})'),
                    ],
                  ),
                ],
              ),
            ),
          ),

          // Tab content
          Expanded(
            child: state.isLoading
                ? const Center(child: CircularProgressIndicator(color: Color(0xFF6C63FF)))
                : TabBarView(
                    controller: _tabController,
                    children: [
                      _ToolsList(tools: state.tools),
                      _SkillsList(skills: state.skills),
                      _SubagentsList(subagents: state.subagents),
                      _McpToolsList(tools: state.mcpTools),
                    ],
                  ),
          ),
        ],
      ),
    );
  }
}

class _ToolsList extends StatelessWidget {
  final List<AgentTool> tools;

  const _ToolsList({required this.tools});

  @override
  Widget build(BuildContext context) {
    if (tools.isEmpty) return _buildEmpty('لا توجد أدوات متاحة', Icons.build);

    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: tools.length,
      itemBuilder: (context, index) => _ToolCard(tool: tools[index]),
    );
  }

  Widget _buildEmpty(String message, IconData icon) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(icon, color: const Color(0xFF6B6B8D), size: 48),
          const SizedBox(height: 16),
          Text(message, style: const TextStyle(color: Color(0xFF6B6B8D), fontSize: 15)),
        ],
      ),
    );
  }
}

class _ToolCard extends StatelessWidget {
  final AgentTool tool;

  const _ToolCard({required this.tool});

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: const Color(0xFF1E1E32),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: const Color(0xFF2A2A45), width: 0.5),
      ),
      child: Row(
        children: [
          Container(
            width: 42,
            height: 42,
            decoration: BoxDecoration(
              color: tool.isEnabled
                  ? const Color(0xFF6C63FF).withValues(alpha: 0.12)
                  : const Color(0xFF2A2A45),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Icon(
              Icons.build_circle,
              color: tool.isEnabled ? const Color(0xFF6C63FF) : const Color(0xFF6B6B8D),
              size: 22,
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  tool.name,
                  style: TextStyle(
                    color: tool.isEnabled ? Colors.white : const Color(0xFF6B6B8D),
                    fontSize: 14,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                if (tool.description != null) ...[
                  const SizedBox(height: 4),
                  Text(
                    tool.description!,
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(color: Color(0xFF6B6B8D), fontSize: 12),
                  ),
                ],
              ],
            ),
          ),
          if (tool.category != null) ...[
            const SizedBox(width: 8),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
              decoration: BoxDecoration(
                color: const Color(0xFF2A2A45),
                borderRadius: BorderRadius.circular(4),
              ),
              child: Text(
                tool.category!,
                style: const TextStyle(color: Color(0xFF6B6B8D), fontSize: 10),
              ),
            ),
          ],
        ],
      ),
    );
  }
}

class _SkillsList extends StatelessWidget {
  final List<Skill> skills;

  const _SkillsList({required this.skills});

  @override
  Widget build(BuildContext context) {
    if (skills.isEmpty) return _buildEmpty('لا توجد مهارات متاحة', Icons.auto_awesome);

    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: skills.length,
      itemBuilder: (context, index) {
        final skill = skills[index];
        return Container(
          margin: const EdgeInsets.only(bottom: 10),
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            color: const Color(0xFF1E1E32),
            borderRadius: BorderRadius.circular(14),
            border: Border.all(color: const Color(0xFF2A2A45), width: 0.5),
          ),
          child: Row(
            children: [
              Container(
                width: 42,
                height: 42,
                decoration: BoxDecoration(
                  gradient: skill.isEnabled ? AppTheme.primaryGradient : null,
                  color: skill.isEnabled ? null : const Color(0xFF2A2A45),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Icon(
                  Icons.auto_awesome,
                  color: skill.isEnabled ? Colors.white : const Color(0xFF6B6B8D),
                  size: 22,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Text(
                          skill.name,
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 14,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                        if (skill.version != null) ...[
                          const SizedBox(width: 6),
                          Text(
                            'v${skill.version}',
                            style: const TextStyle(
                              color: Color(0xFF6B6B8D),
                              fontSize: 10,
                            ),
                          ),
                        ],
                      ],
                    ),
                    if (skill.description != null) ...[
                      const SizedBox(height: 4),
                      Text(
                        skill.description!,
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(color: Color(0xFF6B6B8D), fontSize: 12),
                      ),
                    ],
                  ],
                ),
              ),
            ],
          ),
        );
      },
    );
  }

  Widget _buildEmpty(String message, IconData icon) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(icon, color: const Color(0xFF6B6B8D), size: 48),
          const SizedBox(height: 16),
          Text(message, style: const TextStyle(color: Color(0xFF6B6B8D), fontSize: 15)),
        ],
      ),
    );
  }
}

class _SubagentsList extends StatelessWidget {
  final List<Subagent> subagents;

  const _SubagentsList({required this.subagents});

  @override
  Widget build(BuildContext context) {
    if (subagents.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.smart_toy, color: Color(0xFF6B6B8D), size: 48),
            const SizedBox(height: 16),
            const Text('لا يوجد وكلاء فرعيين', style: TextStyle(color: Color(0xFF6B6B8D), fontSize: 15)),
          ],
        ),
      );
    }

    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: subagents.length,
      itemBuilder: (context, index) {
        final agent = subagents[index];
        final statusColor = Helpers.getStatusColor(agent.status);
        final statusIcon = Helpers.getStatusIcon(agent.status);

        return Container(
          margin: const EdgeInsets.only(bottom: 10),
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            color: const Color(0xFF1E1E32),
            borderRadius: BorderRadius.circular(14),
            border: Border.all(color: const Color(0xFF2A2A45), width: 0.5),
          ),
          child: Row(
            children: [
              Container(
                width: 42,
                height: 42,
                decoration: BoxDecoration(
                  color: statusColor.withValues(alpha: 0.12),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Icon(statusIcon, color: statusColor, size: 22),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      agent.name,
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 14,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                    if (agent.description != null) ...[
                      const SizedBox(height: 4),
                      Text(
                        agent.description!,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(color: Color(0xFF6B6B8D), fontSize: 12),
                      ),
                    ],
                  ],
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                decoration: BoxDecoration(
                  color: statusColor.withValues(alpha: 0.1),
                  borderRadius: BorderRadius.circular(6),
                ),
                child: Text(
                  agent.status,
                  style: TextStyle(
                    color: statusColor,
                    fontSize: 11,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
            ],
          ),
        );
      },
    );
  }
}

class _McpToolsList extends StatelessWidget {
  final List<McpTool> tools;

  const _McpToolsList({required this.tools});

  @override
  Widget build(BuildContext context) {
    if (tools.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.extension, color: Color(0xFF6B6B8D), size: 48),
            const SizedBox(height: 16),
            const Text('لا توجد أدوات MCP', style: TextStyle(color: Color(0xFF6B6B8D), fontSize: 15)),
          ],
        ),
      );
    }

    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: tools.length,
      itemBuilder: (context, index) {
        final tool = tools[index];
        return Container(
          margin: const EdgeInsets.only(bottom: 10),
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            color: const Color(0xFF1E1E32),
            borderRadius: BorderRadius.circular(14),
            border: Border.all(color: const Color(0xFF2A2A45), width: 0.5),
          ),
          child: Row(
            children: [
              Container(
                width: 42,
                height: 42,
                decoration: BoxDecoration(
                  color: const Color(0xFF00D9FF).withValues(alpha: 0.1),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: const Icon(Icons.extension, color: Color(0xFF00D9FF), size: 22),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      tool.name,
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 14,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                    if (tool.description != null) ...[
                      const SizedBox(height: 4),
                      Text(
                        tool.description!,
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(color: Color(0xFF6B6B8D), fontSize: 12),
                      ),
                    ],
                    if (tool.server != null) ...[
                      const SizedBox(height: 4),
                      Text(
                        tool.server!,
                        style: const TextStyle(
                          color: Color(0xFF00D9FF),
                          fontSize: 11,
                        ),
                      ),
                    ],
                  ],
                ),
              ),
            ],
          ),
        );
      },
    );
  }
}
