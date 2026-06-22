import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import 'package:markdown/markdown.dart' as md;
import 'package:share_plus/share_plus.dart';
import '../../../core/theme/app_theme.dart';
import '../../../core/utils/extensions.dart';
import '../../../models/chat_message.dart';
import 'code_block.dart';

class MessageBubble extends StatelessWidget {
  final ChatMessage message;
  final VoidCallback? onDelete;
  final VoidCallback? onRetry;

  const MessageBubble({
    super.key,
    required this.message,
    this.onDelete,
    this.onRetry,
  });

  @override
  Widget build(BuildContext context) {
    final isUser = message.role == MessageRole.user;
    final isSystem = message.role == MessageRole.system;

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisAlignment: isUser ? MainAxisAlignment.end : MainAxisAlignment.start,
        children: [
          if (!isUser) _buildAvatar(isSystem),
          if (!isUser) const SizedBox(width: 8),
          Flexible(
            child: Container(
              constraints: BoxConstraints(
                maxWidth: context.screenWidth * 0.75,
              ),
              decoration: BoxDecoration(
                gradient: isUser
                    ? const LinearGradient(
                        colors: [Color(0xFF6C63FF), Color(0xFF5A52E0)],
                        begin: Alignment.topLeft,
                        end: Alignment.bottomRight,
                      )
                    : isSystem
                        ? null
                        : const LinearGradient(
                            colors: [Color(0xFF1E1E32), Color(0xFF22223A)],
                            begin: Alignment.topLeft,
                            end: Alignment.bottomRight,
                          ),
                color: isSystem ? const Color(0xFF2A2A45) : null,
                borderRadius: BorderRadius.only(
                  topLeft: const Radius.circular(18),
                  topRight: const Radius.circular(18),
                  bottomLeft: isUser
                      ? const Radius.circular(18)
                      : const Radius.circular(4),
                  bottomRight: isUser
                      ? const Radius.circular(4)
                      : const Radius.circular(18),
                ),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withValues(alpha: 0.15),
                    blurRadius: 8,
                    offset: const Offset(0, 2),
                  ),
                ],
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Message content
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                    child: _buildContent(isUser),
                  ),

                  // Tool calls indicator
                  if (message.toolCalls != null && message.toolCalls!.isNotEmpty)
                    _buildToolCalls(),

                  // Error indicator
                  if (message.status == MessageStatus.error)
                    _buildErrorIndicator(),

                  // Actions bar
                  _buildActions(isUser),
                ],
              ),
            ),
          ),
          if (isUser) const SizedBox(width: 8),
          if (isUser) _buildAvatar(isSystem),
        ],
      ),
    );
  }

  Widget _buildAvatar(bool isSystem) {
    if (message.role == MessageRole.user) {
      return Container(
        width: 36,
        height: 36,
        decoration: BoxDecoration(
          gradient: const LinearGradient(
            colors: [Color(0xFF00D9FF), Color(0xFF00B8D9)],
          ),
          borderRadius: BorderRadius.circular(12),
        ),
        child: const Icon(Icons.person, color: Colors.white, size: 18),
      );
    }

    return Container(
      width: 36,
      height: 36,
      decoration: BoxDecoration(
        gradient: AppTheme.primaryGradient,
        borderRadius: BorderRadius.circular(12),
      ),
      child: const Icon(Icons.auto_awesome, color: Colors.white, size: 18),
    );
  }

  Widget _buildContent(bool isUser) {
    if (isUser) {
      return SelectableText(
        message.content,
        style: const TextStyle(
          color: Colors.white,
          fontSize: 15,
          height: 1.6,
          fontWeight: FontWeight.w400,
        ),
      );
    }

    // Parse and render markdown for assistant messages
    return MarkdownBody(
      data: message.content,
      selectable: true,
      builders: {
        'code': _CodeBlockBuilder(),
      },
      styleSheet: MarkdownStyleSheet(
        p: const TextStyle(
          color: Colors.white,
          fontSize: 15,
          height: 1.7,
        ),
        h1: const TextStyle(
          color: Colors.white,
          fontSize: 22,
          fontWeight: FontWeight.w700,
        ),
        h2: const TextStyle(
          color: Colors.white,
          fontSize: 19,
          fontWeight: FontWeight.w600,
        ),
        h3: const TextStyle(
          color: Colors.white,
          fontSize: 17,
          fontWeight: FontWeight.w600,
        ),
        code: TextStyle(
          color: const Color(0xFF00D9FF),
          backgroundColor: const Color(0xFF0D0D1A),
          fontSize: 13,
          fontFamily: 'JetBrains Mono',
        ),
        codeblockDecoration: BoxDecoration(
          color: const Color(0xFF0D0D1A),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: const Color(0xFF2A2A45), width: 0.5),
        ),
        blockquote: const TextStyle(
          color: Color(0xFF9E9EB8),
          fontSize: 14,
          fontStyle: FontStyle.italic,
        ),
        blockquoteDecoration: BoxDecoration(
          color: const Color(0xFF6C63FF).withValues(alpha: 0.05),
          borderRadius: BorderRadius.circular(8),
          border: Border(
            left: BorderSide(color: const Color(0xFF6C63FF), width: 3),
          ),
        ),
        listBullet: const TextStyle(color: Color(0xFF6C63FF)),
        tableHead: const TextStyle(
          color: Colors.white,
          fontWeight: FontWeight.w600,
        ),
        tableBody: const TextStyle(color: Color(0xFFE0E0EE)),
        tableBorder: TableBorder.all(
          color: const Color(0xFF2A2A45),
          width: 0.5,
        ),
        a: const TextStyle(
          color: Color(0xFF00D9FF),
          decoration: TextDecoration.underline,
        ),
        em: const TextStyle(
          color: Color(0xFF9E9EB8),
          fontStyle: FontStyle.italic,
        ),
        strong: const TextStyle(
          color: Colors.white,
          fontWeight: FontWeight.w700,
        ),
      ),
    );
  }

  Widget _buildToolCalls() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      decoration: const BoxDecoration(
        border: Border(
          top: BorderSide(color: Color(0xFF2A2A45), width: 0.5),
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: message.toolCalls!.map((tc) => _ToolCallItem(toolCall: tc)).toList(),
      ),
    );
  }

  Widget _buildErrorIndicator() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      decoration: const BoxDecoration(
        border: Border(
          top: BorderSide(color: Color(0xFFFF5252), width: 0.5),
        ),
      ),
      child: Row(
        children: [
          const Icon(Icons.error_outline, color: Color(0xFFFF5252), size: 16),
          const SizedBox(width: 8),
          const Expanded(
            child: Text(
              'فشل إرسال الرسالة',
              style: TextStyle(color: Color(0xFFFF5252), fontSize: 13),
            ),
          ),
          if (onRetry != null)
            TextButton(
              onPressed: onRetry,
              child: const Text('إعادة', style: TextStyle(fontSize: 12)),
            ),
        ],
      ),
    );
  }

  Widget _buildActions(bool isUser) {
    return Container(
      padding: const EdgeInsets.only(left: 12, right: 12, bottom: 8, top: 4),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          // Copy
          _ActionButton(
            icon: Icons.copy_outlined,
            tooltip: 'نسخ',
            onTap: () {
              Clipboard.setData(ClipboardData(text: message.content));
            },
          ),
          const SizedBox(width: 4),
          // Share
          _ActionButton(
            icon: Icons.share_outlined,
            tooltip: 'مشاركة',
            onTap: () {
              Share.share(message.content);
            },
          ),
          if (onDelete != null) ...[
            const SizedBox(width: 4),
            _ActionButton(
              icon: Icons.delete_outline,
              tooltip: 'حذف',
              onTap: onDelete!,
            ),
          ],
          const Spacer(),
          // Timestamp
          Text(
            message.timestamp.formattedTime,
            style: TextStyle(
              color: isUser ? Colors.white30 : const Color(0xFF4A4A6A),
              fontSize: 11,
            ),
          ),
        ],
      ),
    );
  }
}

class _ActionButton extends StatelessWidget {
  final IconData icon;
  final String tooltip;
  final VoidCallback onTap;

  const _ActionButton({
    required this.icon,
    required this.tooltip,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(8),
        child: Padding(
          padding: const EdgeInsets.all(4),
          child: Icon(icon, size: 16, color: const Color(0xFF6B6B8D)),
        ),
      ),
    );
  }
}

class _ToolCallItem extends StatelessWidget {
  final ToolCall toolCall;

  const _ToolCallItem({required this.toolCall});

  @override
  Widget build(BuildContext context) {
    final isRunning = toolCall.status == ToolCallStatus.running;
    final isCompleted = toolCall.status == ToolCallStatus.completed;
    final isFailed = toolCall.status == ToolCallStatus.failed;

    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        children: [
          if (isRunning)
            const SizedBox(
              width: 14,
              height: 14,
              child: CircularProgressIndicator(
                strokeWidth: 2,
                color: Color(0xFF6C63FF),
              ),
            )
          else
            Icon(
              isCompleted ? Icons.check_circle : Icons.error,
              size: 14,
              color: isCompleted ? const Color(0xFF00E676) : const Color(0xFFFF5252),
            ),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              isRunning ? 'جاري استخدام: ${toolCall.name}' : toolCall.name,
              style: TextStyle(
                color: isRunning
                    ? const Color(0xFF6C63FF)
                    : isCompleted
                        ? const Color(0xFF00E676)
                        : const Color(0xFFFF5252),
                fontSize: 12,
                fontWeight: FontWeight.w500,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _CodeBlockBuilder extends MarkdownElementBuilder {
  @override
  Widget visitElementAfterWithContext(BuildContext context, md.Element element, _, __) {
    final code = element.textContent;
    final language = element.attributes['class']?.replaceFirst('language-', '') ?? '';
    return CodeBlock(code: code, language: language);
  }
}


