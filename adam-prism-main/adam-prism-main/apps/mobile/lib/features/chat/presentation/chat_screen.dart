import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/theme/app_theme.dart';
import '../providers/chat_provider.dart';
import '../widgets/message_bubble.dart';
import '../widgets/streaming_message.dart';
import '../widgets/chat_input.dart';
import '../widgets/tool_indicator.dart';
import '../../sessions/providers/sessions_provider.dart';

class ChatScreen extends ConsumerStatefulWidget {
  const ChatScreen({super.key});

  @override
  ConsumerState<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends ConsumerState<ChatScreen> {
  final _scrollController = ScrollController();

  @override
  void dispose() {
    _scrollController.dispose();
    super.dispose();
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOutCubic,
        );
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final chatState = ref.watch(chatProvider);

    // Auto-scroll when streaming
    ref.listen(chatProvider, (prev, next) {
      if (next.streamingContent.isNotEmpty || next.messages.length != (prev?.messages.length ?? 0)) {
        _scrollToBottom();
      }
    });

    return Container(
      decoration: const BoxDecoration(
        color: Color(0xFF0F0F1A),
      ),
      child: Column(
        children: [
          // Custom app bar
          _buildAppBar(chatState),

          // Messages
          Expanded(
            child: chatState.isLoading
                ? const Center(
                    child: CircularProgressIndicator(color: Color(0xFF6C63FF)),
                  )
                : chatState.messages.isEmpty && !chatState.isStreaming
                    ? _buildEmptyState()
                    : RefreshIndicator(
                        color: const Color(0xFF6C63FF),
                        backgroundColor: const Color(0xFF1E1E32),
                        onRefresh: () async {
                          if (chatState.currentSessionId != null) {
                            ref.read(chatProvider.notifier).setSession(chatState.currentSessionId);
                          }
                        },
                        child: ListView.builder(
                          controller: _scrollController,
                          padding: const EdgeInsets.symmetric(vertical: 16),
                          itemCount: chatState.messages.length + (chatState.isStreaming ? 1 : 0),
                          itemBuilder: (context, index) {
                            if (index == chatState.messages.length && chatState.isStreaming) {
                              return StreamingMessage(
                                content: chatState.streamingContent,
                                activeToolCalls: chatState.activeToolCalls,
                              );
                            }
                            final message = chatState.messages[index];
                            return Dismissible(
                              key: ValueKey(message.id),
                              direction: DismissDirection.horizontal,
                              confirmDismiss: (direction) async {
                                if (direction == DismissDirection.endToStart) {
                                  return await _confirmDelete(message.id);
                                }
                                // Share
                                return false;
                              },
                              background: Container(
                                color: const Color(0xFF00D9FF).withValues(alpha: 0.2),
                                alignment: Alignment.centerRight,
                                padding: const EdgeInsets.only(right: 20),
                                child: const Icon(Icons.share, color: Color(0xFF00D9FF)),
                              ),
                              secondaryBackground: Container(
                                color: const Color(0xFFFF5252).withValues(alpha: 0.2),
                                alignment: Alignment.centerLeft,
                                padding: const EdgeInsets.only(left: 20),
                                child: const Icon(Icons.delete, color: Color(0xFFFF5252)),
                              ),
                              child: MessageBubble(
                                message: message,
                                onDelete: () => ref.read(chatProvider.notifier).deleteMessage(message.id),
                                onRetry: message.status == MessageStatus.error
                                    ? () => ref.read(chatProvider.notifier).retryLastMessage()
                                    : null,
                              ),
                            );
                          },
                        ),
                      ),
          ),

          // Error banner
          if (chatState.error != null)
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              color: const Color(0xFFFF5252).withValues(alpha: 0.1),
              child: Row(
                children: [
                  const Icon(Icons.error_outline, color: Color(0xFFFF5252), size: 18),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      chatState.error!,
                      style: const TextStyle(color: Color(0xFFFF5252), fontSize: 13),
                    ),
                  ),
                  TextButton(
                    onPressed: () => ref.read(chatProvider.notifier).retryLastMessage(),
                    child: const Text('إعادة', style: TextStyle(fontSize: 12)),
                  ),
                ],
              ),
            ),

          // Active tool calls
          if (chatState.activeToolCalls.isNotEmpty)
            ...chatState.activeToolCalls.map(
              (tc) => ToolIndicator(
                toolName: tc.name,
                status: tc.status == ToolCallStatus.running
                    ? 'running'
                    : tc.status == ToolCallStatus.completed
                        ? 'completed'
                        : 'failed',
              ),
            ),

          // Chat input
          ChatInput(
            onSend: (text) => ref.read(chatProvider.notifier).sendMessage(text),
            isStreaming: chatState.isStreaming,
            onStop: () {
              ref.read(chatProvider.notifier).clearChat();
            },
          ),
        ],
      ),
    );
  }

  Widget _buildAppBar(ChatState chatState) {
    return Container(
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [
            const Color(0xFF1A1A2E),
            const Color(0xFF1A1A2E).withValues(alpha: 0.95),
          ],
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
        ),
        border: Border(
          bottom: BorderSide(
            color: const Color(0xFF2A2A45),
            width: 0.5,
          ),
        ),
      ),
      child: SafeArea(
        bottom: false,
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
          child: Row(
            children: [
              // Menu / Back
              IconButton(
                icon: const Icon(Icons.menu, color: Colors.white),
                onPressed: () {
                  Scaffold.of(context).openDrawer();
                },
              ),

              // Title
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      chatState.currentSessionId != null ? 'محادثة' : 'محادثة جديدة',
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 17,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                    Row(
                      children: [
                        Container(
                          width: 8,
                          height: 8,
                          decoration: BoxDecoration(
                            color: chatState.isStreaming
                                ? const Color(0xFF00E676)
                                : const Color(0xFF6B6B8D),
                            borderRadius: BorderRadius.circular(4),
                          ),
                        ),
                        const SizedBox(width: 6),
                        Text(
                          chatState.isStreaming
                              ? 'جاري الكتابة...'
                              : 'آدم بريزم',
                          style: TextStyle(
                            color: chatState.isStreaming
                                ? const Color(0xFF00E676)
                                : const Color(0xFF6B6B8D),
                            fontSize: 12,
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),

              // New chat
              IconButton(
                icon: Container(
                  padding: const EdgeInsets.all(4),
                  decoration: BoxDecoration(
                    color: const Color(0xFF6C63FF).withValues(alpha: 0.15),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: const Icon(Icons.add, color: Color(0xFF6C63FF), size: 20),
                ),
                onPressed: () {
                  ref.read(chatProvider.notifier).newChat();
                  ref.read(sessionsProvider.notifier).refreshSessions();
                },
              ),

              // More options
              PopupMenuButton<String>(
                icon: const Icon(Icons.more_vert, color: Color(0xFF6B6B8D)),
                color: const Color(0xFF1E1E32),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
                onSelected: (value) {
                  switch (value) {
                    case 'clear':
                      ref.read(chatProvider.notifier).clearChat();
                      break;
                    case 'help':
                      _showHelpDialog();
                      break;
                  }
                },
                itemBuilder: (context) => [
                  const PopupMenuItem(
                    value: 'clear',
                    child: Row(
                      children: [
                        Icon(Icons.clear_all, color: Color(0xFF6B6B8D), size: 20),
                        SizedBox(width: 12),
                        Text('مسح المحادثة', style: TextStyle(color: Colors.white)),
                      ],
                    ),
                  ),
                  const PopupMenuItem(
                    value: 'help',
                    child: Row(
                      children: [
                        Icon(Icons.help_outline, color: Color(0xFF6B6B8D), size: 20),
                        SizedBox(width: 12),
                        Text('الأوامر المتاحة', style: TextStyle(color: Colors.white)),
                      ],
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: SingleChildScrollView(
        padding: const EdgeInsets.symmetric(horizontal: 40),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            // Logo
            Container(
              width: 80,
              height: 80,
              decoration: BoxDecoration(
                gradient: AppTheme.primaryGradient,
                borderRadius: BorderRadius.circular(24),
                boxShadow: [
                  BoxShadow(
                    color: const Color(0xFF6C63FF).withValues(alpha: 0.3),
                    blurRadius: 30,
                  ),
                ],
              ),
              child: const Icon(
                Icons.auto_awesome,
                color: Colors.white,
                size: 40,
              ),
            ),
            const SizedBox(height: 24),

            const Text(
              'مرحباً بك في آدم بريزم',
              style: TextStyle(
                color: Colors.white,
                fontSize: 22,
                fontWeight: FontWeight.w700,
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 8),

            const Text(
              'مساعدك الذكي الشخصي. اسألني أي شيء وسأساعدك!',
              style: TextStyle(
                color: Color(0xFF6B6B8D),
                fontSize: 15,
                height: 1.6,
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 32),

            // Quick actions
            Wrap(
              spacing: 8,
              runSpacing: 8,
              alignment: WrapAlignment.center,
              children: [
                _QuickAction(
                  icon: Icons.lightbulb_outline,
                  label: 'اقترح فكرة مشروع',
                  onTap: () => ref.read(chatProvider.notifier).sendMessage('اقترح لي فكرة مشروع إبداعي'),
                ),
                _QuickAction(
                  icon: Icons.code,
                  label: 'اكتب كود',
                  onTap: () => ref.read(chatProvider.notifier).sendMessage('اكتب لي كود Python لتحليل البيانات'),
                ),
                _QuickAction(
                  icon: Icons.translate,
                  label: 'ترجم نص',
                  onTap: () => ref.read(chatProvider.notifier).sendMessage('ساعدني في ترجمة نص'),
                ),
                _QuickAction(
                  icon: Icons.school,
                  label: 'اشرح مفهوم',
                  onTap: () => ref.read(chatProvider.notifier).sendMessage('اشرح لي مفهوم الذكاء الاصطناعي ببساطة'),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Future<bool?> _confirmDelete(String messageId) {
    return showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: const Color(0xFF1E1E32),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        title: const Text(
          'حذف الرسالة',
          style: TextStyle(color: Colors.white),
        ),
        content: const Text(
          'هل تريد حذف هذه الرسالة؟',
          style: TextStyle(color: Color(0xFF9E9EB8)),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('إلغاء'),
          ),
          TextButton(
            onPressed: () {
              ref.read(chatProvider.notifier).deleteMessage(messageId);
              Navigator.pop(context, true);
            },
            child: const Text('حذف', style: TextStyle(color: Color(0xFFFF5252))),
          ),
        ],
      ),
    );
  }

  void _showHelpDialog() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: const Color(0xFF1E1E32),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        title: Row(
          children: [
            Container(
              width: 36,
              height: 36,
              decoration: BoxDecoration(
                color: const Color(0xFF6C63FF).withValues(alpha: 0.15),
                borderRadius: BorderRadius.circular(10),
              ),
              child: const Icon(Icons.terminal, color: Color(0xFF6C63FF), size: 18),
            ),
            const SizedBox(width: 12),
            const Text('الأوامر المتاحة', style: TextStyle(color: Colors.white)),
          ],
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            _buildCommandItem('/new', 'محادثة جديدة'),
            _buildCommandItem('/clear', 'مسح المحادثة'),
            _buildCommandItem('/memory', 'تصفح الذاكرة'),
            _buildCommandItem('/help', 'عرض الأوامر'),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('تم'),
          ),
        ],
      ),
    );
  }

  Widget _buildCommandItem(String command, String description) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
            decoration: BoxDecoration(
              color: const Color(0xFF0D0D1A),
              borderRadius: BorderRadius.circular(6),
            ),
            child: Text(
              command,
              style: const TextStyle(
                color: Color(0xFF00D9FF),
                fontSize: 13,
                fontFamily: 'monospace',
                fontWeight: FontWeight.w600,
              ),
            ),
          ),
          const SizedBox(width: 12),
          Text(
            description,
            style: const TextStyle(color: Color(0xFF9E9EB8), fontSize: 14),
          ),
        ],
      ),
    );
  }
}

class _QuickAction extends StatelessWidget {
  final IconData icon;
  final String label;
  final VoidCallback onTap;

  const _QuickAction({
    required this.icon,
    required this.label,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
          decoration: BoxDecoration(
            color: const Color(0xFF1E1E32),
            borderRadius: BorderRadius.circular(12),
            border: Border.all(
              color: const Color(0xFF2A2A45),
              width: 0.5,
            ),
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(icon, color: const Color(0xFF6C63FF), size: 16),
              const SizedBox(width: 8),
              Text(
                label,
                style: const TextStyle(
                  color: Color(0xFFE0E0EE),
                  fontSize: 13,
                  fontWeight: FontWeight.w500,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
