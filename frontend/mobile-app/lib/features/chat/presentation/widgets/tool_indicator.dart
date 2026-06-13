import 'package:flutter/material.dart';
import '../../../core/theme/app_theme.dart';

class ToolIndicator extends StatelessWidget {
  final String toolName;
  final String status;
  final String? result;

  const ToolIndicator({
    super.key,
    required this.toolName,
    required this.status,
    this.result,
  });

  @override
  Widget build(BuildContext context) {
    final isRunning = status == 'running' || status == 'pending';
    final isCompleted = status == 'completed';
    final isFailed = status == 'failed';

    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: const Color(0xFF1E1E32),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: isRunning
              ? const Color(0xFF6C63FF).withValues(alpha: 0.5)
              : isCompleted
                  ? const Color(0xFF00E676).withValues(alpha: 0.5)
                  : const Color(0xFFFF5252).withValues(alpha: 0.5),
          width: 0.5,
        ),
      ),
      child: Row(
        children: [
          // Status icon
          if (isRunning)
            const SizedBox(
              width: 18,
              height: 18,
              child: CircularProgressIndicator(
                strokeWidth: 2,
                color: Color(0xFF6C63FF),
              ),
            )
          else
            Icon(
              isCompleted ? Icons.check_circle : Icons.error,
              size: 18,
              color: isCompleted
                  ? const Color(0xFF00E676)
                  : const Color(0xFFFF5252),
            ),
          const SizedBox(width: 10),

          // Tool info
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  isRunning ? 'جاري استخدام: $toolName' : toolName,
                  style: TextStyle(
                    color: isRunning
                        ? const Color(0xFF6C63FF)
                        : isCompleted
                            ? const Color(0xFF00E676)
                            : const Color(0xFFFF5252),
                    fontSize: 13,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                if (result != null)
                  Padding(
                    padding: const EdgeInsets.only(top: 4),
                    child: Text(
                      result!,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                        color: Color(0xFF6B6B8D),
                        fontSize: 12,
                      ),
                    ),
                  ),
              ],
            ),
          ),

          // Expand button
          if (result != null)
            Icon(
              Icons.expand_more,
              color: const Color(0xFF6B6B8D),
              size: 18,
            ),
        ],
      ),
    );
  }
}
