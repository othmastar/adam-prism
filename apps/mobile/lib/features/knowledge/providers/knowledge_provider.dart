import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/api/api_client.dart';
import '../../../models/knowledge.dart';

class KnowledgeState {
  final List<KnowledgeCollection> collections;
  final List<KnowledgeSearchResult> searchResults;
  final bool isLoading;
  final String? error;
  final String searchQuery;

  const KnowledgeState({
    this.collections = const [],
    this.searchResults = const [],
    this.isLoading = false,
    this.error,
    this.searchQuery = '',
  });

  KnowledgeState copyWith({
    List<KnowledgeCollection>? collections,
    List<KnowledgeSearchResult>? searchResults,
    bool? isLoading,
    String? error,
    String? searchQuery,
  }) {
    return KnowledgeState(
      collections: collections ?? this.collections,
      searchResults: searchResults ?? this.searchResults,
      isLoading: isLoading ?? this.isLoading,
      error: error,
      searchQuery: searchQuery ?? this.searchQuery,
    );
  }
}

class KnowledgeNotifier extends StateNotifier<KnowledgeState> {
  KnowledgeNotifier() : super(const KnowledgeState());

  Future<void> loadCollections() async {
    state = state.copyWith(isLoading: true);
    try {
      final json = await ApiClient.instance.getCollections();
      final collections = json.map((c) => KnowledgeCollection.fromApi(c as Map<String, dynamic>)).toList();
      state = state.copyWith(collections: collections, isLoading: false);
    } catch (e) {
      state = state.copyWith(isLoading: false, error: e.toString());
    }
  }

  Future<void> searchKnowledge(String query) async {
    state = state.copyWith(isLoading: true, searchQuery: query);
    try {
      final json = await ApiClient.instance.searchKnowledge(query);
      final results = json.map((r) => KnowledgeSearchResult.fromApi(r as Map<String, dynamic>)).toList();
      state = state.copyWith(searchResults: results, isLoading: false);
    } catch (e) {
      state = state.copyWith(isLoading: false, error: e.toString());
    }
  }

  void clearSearch() {
    state = state.copyWith(searchResults: [], searchQuery: '');
  }
}

final knowledgeProvider = StateNotifierProvider<KnowledgeNotifier, KnowledgeState>(
  (ref) => KnowledgeNotifier(),
);
