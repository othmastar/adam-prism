import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/theme/app_theme.dart';
import '../providers/sessions_provider.dart';
import '../widgets/session_item.dart';
import '../widgets/session_search.dart';
import '../../chat/providers/chat_provider.dart';

class SessionsScreen extends ConsumerStatefulWidget {
  const SessionsScreen({super.key});

  @override
  ConsumerState<SessionsScreen> createState() => _SessionsScreenState();
}

class _SessionsScreenState extends ConsumerState<SessionsScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      ref.read(sessionsProvider.notifier).loadSessions();
    });
  }

  @override
  Widget build(BuildContext context) {
    final sessionsState = ref.watch(sessionsProvider);

    return Container(
      decoration: const BoxDecoration(
        color: Color(0xFF0F0F1A),
      ),
      child: Column(
        children: [
          // Header
          Container(
            padding: const EdgeInsets.fromLTRB(20, 16, 20, 8),
            decoration: const BoxDecoration(
              color: Color(0xFF1A1A2E),
              border: Border(
                bottom: BorderSide(color: Color(0xFF2A2A45), width: 0.5),
              ),
            ),
            child: SafeArea(
              bottom: false,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      const Text(
                        'المحادثات',
                        style: TextStyle(
                          color: Colors.white,
                          fontSize: 24,
                          fontWeight: FontWeight.w800,
                        ),
                      ),
                      const Spacer(),
                      // New chat button
                      Container(
                        decoration: BoxDecoration(
                          gradient: AppTheme.primaryGradient,
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: Material(
                          color: Colors.transparent,
                          child: InkWell(
                            onTap: () {
                              ref.read(chatProvider.notifier).newChat();
                            },
                            borderRadius: BorderRadius.circular(12),
                            child: const Padding(
                              padding: EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                              child: Row(
                                mainAxisSize: MainAxisSize.min,
                                children: [
                                  Icon(Icons.add, color: Colors.white, size: 18),
                                  SizedBox(width: 6),
                                  Text(
                                    'جديد',
                                    style: TextStyle(
                                      color: Colors.white,
                                      fontSize: 13,
                                      fontWeight: FontWeight.w600,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          ),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),

          // Search
          SessionSearch(
            onSearch: (query) {
              ref.read(sessionsProvider.notifier).searchSessions(query);
            },
            onClear: () {
              ref.read(sessionsProvider.notifier).setSearchQuery('');
              ref.read(sessionsProvider.notifier).loadSessions();
            },
          ),

          // Sessions list
          Expanded(
            child: sessionsState.isLoading
                ? const Center(
                    child: CircularProgressIndicator(color: Color(0xFF6C63FF)),
                  )
                : sessionsState.sessions.isEmpty
                    ? _buildEmptyState()
                    : RefreshIndicator(
                        color: const Color(0xFF6C63FF),
                        backgroundColor: const Color(0xFF1E1E32),
                        onRefresh: () => ref.read(sessionsProvider.notifier).refreshSessions(),
                        child: _buildSessionList(sessionsState),
                      ),
          ),
        ],
      ),
    );
  }

  Widget _buildSessionList(SessionsState state) {
    final groups = state.groupedSessions;
    final groupOrder = ['اليوم', 'أمس', 'هذا الأسبوع', 'هذا الشهر', 'أقدم'];

    return ListView.builder(
      padding: const EdgeInsets.only(bottom: 80),
      itemCount: groups.length,
      itemBuilder: (context, index) {
        final key = groupOrder.firstWhere(
          (k) => groups.containsKey(k),
          orElse: () => groups.keys.elementAt(index),
        );
        final sessions = groups[key] ?? [];

        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Group header
            Padding(
              padding: const EdgeInsets.fromLTRB(20, 16, 20, 8),
              child: Text(
                key,
                style: const TextStyle(
                  color: Color(0xFF6B6B8D),
                  fontSize: 13,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
            // Sessions in this group
            ...sessions.map(
              (session) => SessionItem(
                session: session,
                onTap: () {
                  ref.read(chatProvider.notifier).setSession(session.id);
                },
                onDelete: () {
                  ref.read(sessionsProvider.notifier).deleteSession(session.id);
                },
              ),
            ),
          ],
        );
      },
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 40),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              width: 80,
              height: 80,
              decoration: BoxDecoration(
                color: const Color(0xFF1E1E32),
                borderRadius: BorderRadius.circular(24),
              ),
              child: const Icon(
                Icons.chat_bubble_outline,
                color: Color(0xFF6B6B8D),
                size: 36,
              ),
            ),
            const SizedBox(height: 20),
            const Text(
              'لا توجد محادثات',
              style: TextStyle(
                color: Colors.white,
                fontSize: 18,
                fontWeight: FontWeight.w600,
              ),
            ),
            const SizedBox(height: 8),
            const Text(
              'ابدأ محادثة جديدة مع آدم بريزم',
              style: TextStyle(
                color: Color(0xFF6B6B8D),
                fontSize: 14,
              ),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }
}
