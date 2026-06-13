import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/api/api_client.dart';
import '../../../models/session.dart';

class SessionsState {
  final List<Session> sessions;
  final bool isLoading;
  final String? error;
  final String searchQuery;

  const SessionsState({
    this.sessions = const [],
    this.isLoading = false,
    this.error,
    this.searchQuery = '',
  });

  SessionsState copyWith({
    List<Session>? sessions,
    bool? isLoading,
    String? error,
    String? searchQuery,
  }) {
    return SessionsState(
      sessions: sessions ?? this.sessions,
      isLoading: isLoading ?? this.isLoading,
      error: error,
      searchQuery: searchQuery ?? this.searchQuery,
    );
  }

  List<Session> get filteredSessions {
    if (searchQuery.isEmpty) return sessions;
    return sessions.where((s) =>
      s.title.toLowerCase().contains(searchQuery.toLowerCase()) ||
      (s.preview?.toLowerCase().contains(searchQuery.toLowerCase()) ?? false)
    ).toList();
  }

  Map<String, List<Session>> get groupedSessions {
    final sorted = List<Session>.from(filteredSessions)
      ..sort((a, b) => b.updatedAt.compareTo(a.updatedAt));

    final groups = <String, List<Session>>{};
    for (final session in sorted) {
      final key = session.updatedAt.groupLabel;
      groups.putIfAbsent(key, () => []).add(session);
    }
    return groups;
  }
}

extension on DateTime {
  String get groupLabel {
    final now = DateTime.now();
    if (year == now.year && month == now.month && day == now.day) return 'اليوم';
    final yesterday = now.subtract(const Duration(days: 1));
    if (year == yesterday.year && month == yesterday.month && day == yesterday.day) return 'أمس';
    if (now.difference(this).inDays < 7) return 'هذا الأسبوع';
    if (now.difference(this).inDays < 30) return 'هذا الشهر';
    return 'أقدم';
  }
}

class SessionsNotifier extends StateNotifier<SessionsState> {
  SessionsNotifier() : super(const SessionsState());

  Future<void> loadSessions() async {
    state = state.copyWith(isLoading: true);
    try {
      final sessionsJson = await ApiClient.instance.getSessions();
      final sessions = sessionsJson.map((s) => Session.fromApi(s as Map<String, dynamic>)).toList();
      state = state.copyWith(sessions: sessions, isLoading: false);
    } catch (e) {
      state = state.copyWith(isLoading: false, error: e.toString());
    }
  }

  Future<void> refreshSessions() async {
    await loadSessions();
  }

  void setSearchQuery(String query) {
    state = state.copyWith(searchQuery: query);
  }

  Future<void> deleteSession(String sessionId) async {
    try {
      await ApiClient.instance.deleteSession(sessionId);
      state = state.copyWith(
        sessions: state.sessions.where((s) => s.id != sessionId).toList(),
      );
    } catch (e) {
      state = state.copyWith(error: e.toString());
    }
  }

  Future<void> searchSessions(String query) async {
    if (query.isEmpty) {
      state = state.copyWith(searchQuery: '');
      await loadSessions();
      return;
    }
    state = state.copyWith(isLoading: true, searchQuery: query);
    try {
      final results = await ApiClient.instance.searchSessions(query);
      final sessions = results.map((s) => Session.fromApi(s as Map<String, dynamic>)).toList();
      state = state.copyWith(sessions: sessions, isLoading: false);
    } catch (e) {
      state = state.copyWith(isLoading: false, error: e.toString());
    }
  }
}

final sessionsProvider = StateNotifierProvider<SessionsNotifier, SessionsState>(
  (ref) => SessionsNotifier(),
);
