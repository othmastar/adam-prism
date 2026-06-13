import 'package:flutter/material.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../models/session.dart';

class SessionItem extends StatelessWidget {
  final Session session;
  final VoidCallback onTap;
  final VoidCallback onDelete;

  const SessionItem({
    super.key,
    required this.session,
    required this.onTap,
    required this.onDelete,
  });

  @override
  Widget build(BuildContext context) {
    return Dismissible(
      key: ValueKey(session.id),
      direction: DismissDirection.endToStart,
      confirmDismiss: (_) async {
        return await showDialog<bool>(
          context: context,
          builder: (context) => AlertDialog(
            backgroundColor: const Color(0xFF1E1E32),
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
            title: const Text('حذف المحادثة', style: TextStyle(color: Colors.white)),
            content: const Text(
              'هل تريد حذف هذه المحادثة؟ لا يمكن التراجع عن هذا الإجراء.',
              style: TextStyle(color: Color(0xFF9E9EB8)),
            ),
            actions: [
              TextButton(
                onPressed: () => Navigator.pop(context, false),
                child: const Text('إلغاء'),
              ),
              TextButton(
                onPressed: () => Navigator.pop(context, true),
                child: const Text('حذف', style: TextStyle(color: Color(0xFFFF5252))),
              ),
            ],
          ),
        );
      },
      onDismissed: (_) => onDelete(),
      background: Container(
        alignment: Alignment.centerLeft,
        padding: const EdgeInsets.only(left: 20),
        color: const Color(0xFFFF5252).withValues(alpha: 0.2),
        child: const Icon(Icons.delete, color: Color(0xFFFF5252)),
      ),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(12),
          child: Container(
            margin: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: const Color(0xFF1E1E32),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(
                color: const Color(0xFF2A2A45),
                width: 0.5,
              ),
            ),
            child: Row(
              children: [
                // Chat icon
                Container(
                  width: 42,
                  height: 42,
                  decoration: BoxDecoration(
                    gradient: session.isPinned
                        ? AppTheme.primaryGradient
                        : null,
                    color: session.isPinned
                        ? null
                        : const Color(0xFF2A2A45),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Icon(
                    session.isPinned ? Icons.push_pin : Icons.chat_bubble_outline,
                    color: session.isPinned ? Colors.white : const Color(0xFF6B6B8D),
                    size: 20,
                  ),
                ),
                const SizedBox(width: 12),

                // Content
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        session.title,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 15,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                      if (session.preview != null && session.preview!.isNotEmpty) ...[
                        const SizedBox(height: 4),
                        Text(
                          session.preview!,
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: const TextStyle(
                            color: Color(0xFF6B6B8D),
                            fontSize: 13,
                          ),
                        ),
                      ],
                    ],
                  ),
                ),

                const SizedBox(width: 8),

                // Meta
                Column(
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
                    Text(
                      _formatTime(session.updatedAt),
                      style: const TextStyle(
                        color: Color(0xFF4A4A6A),
                        fontSize: 11,
                      ),
                    ),
                    if (session.messageCount > 0)
                      Container(
                        margin: const EdgeInsets.only(top: 4),
                        padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                        decoration: BoxDecoration(
                          color: const Color(0xFF6C63FF).withValues(alpha: 0.1),
                          borderRadius: BorderRadius.circular(6),
                        ),
                        child: Text(
                          '${session.messageCount}',
                          style: const TextStyle(
                            color: Color(0xFF6C63FF),
                            fontSize: 10,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  String _formatTime(DateTime dt) {
    final now = DateTime.now();
    if (dt.year == now.year && dt.month == now.month && dt.day == now.day) {
      return '${dt.hour.toString().padLeft(2, '0')}:${dt.minute.toString().padLeft(2, '0')}';
    }
    final yesterday = now.subtract(const Duration(days: 1));
    if (dt.year == yesterday.year && dt.month == yesterday.month && dt.day == yesterday.day) {
      return 'أمس';
    }
    return '${dt.month}/${dt.day}';
  }
}
