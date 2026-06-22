import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/api/api_client.dart';
import '../../../models/memory.dart';

class MemoryState {
  final MemoryStats? stats;
  final List<MemoryEntry> memories;
  final bool isLoading;
  final String? error;
  final String searchQuery;

  const MemoryState({
    this.stats,
    this.memories = const [],
    this.isLoading = false,
    this.error,
    this.searchQuery = '',
  });

  MemoryState copyWith({
    MemoryStats? stats,
    List<MemoryEntry>? memories,
    bool? isLoading,
    String? error,
    String? searchQuery,
  }) {
    return MemoryState(
      stats: stats ?? this.stats,
      memories: memories ?? this.memories,
      isLoading: isLoading ?? this.isLoading,
      error: error,
      searchQuery: searchQuery ?? this.searchQuery,
    );
  }
}

class MemoryNotifier extends StateNotifier<MemoryState> {
  MemoryNotifier() : super(const MemoryState());

  Future<void> loadStats() async {
    try {
      final json = await ApiClient.instance.getMemoryStats();
      state = state.copyWith(stats: MemoryStats.fromApi(json));
    } catch (e) {
      state = state.copyWith(error: e.toString());
    }
  }

  Future<void> searchMemory(String query) async {
    state = state.copyWith(isLoading: true, searchQuery: query);
    try {
      final json = await ApiClient.instance.searchMemory(query);
      final memories = json.map((m) => MemoryEntry.fromApi(m as Map<String, dynamic>)).toList();
      state = state.copyWith(memories: memories, isLoading: false);
    } catch (e) {
      state = state.copyWith(isLoading: false, error: e.toString());
    }
  }

  Future<void> storeMemory({
    required String content,
    String? category,
    Map<String, dynamic>? metadata,
  }) async {
    try {
      await ApiClient.instance.storeMemory(
        content: content,
        category: category,
        metadata: metadata,
      );
      await loadStats();
    } catch (e) {
      state = state.copyWith(error: e.toString());
    }
  }

  void clearSearch() {
    state = state.copyWith(memories: [], searchQuery: '');
  }
}

final memoryProvider = StateNotifierProvider<MemoryNotifier, MemoryState>(
  (ref) => MemoryNotifier(),
);
