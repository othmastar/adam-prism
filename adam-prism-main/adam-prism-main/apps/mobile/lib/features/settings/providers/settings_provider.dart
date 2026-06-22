import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/api/api_client.dart';
import '../../../core/storage/local_storage.dart';
import '../../../core/constants/app_constants.dart';

class SettingsState {
  final String backendUrl;
  final String apiKey;
  final String themeMode;
  final String locale;
  final String selectedModel;
  final bool voiceInputEnabled;
  final bool voiceOutputEnabled;
  final bool notificationsEnabled;
  final List<String> availableModels;
  final bool isTestingConnection;
  final bool connectionSuccess;
  final String? error;

  const SettingsState({
    this.backendUrl = AppConstants.defaultBackendUrl,
    this.apiKey = '',
    this.themeMode = 'dark',
    this.locale = 'ar',
    this.selectedModel = '',
    this.voiceInputEnabled = true,
    this.voiceOutputEnabled = true,
    this.notificationsEnabled = true,
    this.availableModels = const [],
    this.isTestingConnection = false,
    this.connectionSuccess = false,
    this.error,
  });

  SettingsState copyWith({
    String? backendUrl,
    String? apiKey,
    String? themeMode,
    String? locale,
    String? selectedModel,
    bool? voiceInputEnabled,
    bool? voiceOutputEnabled,
    bool? notificationsEnabled,
    List<String>? availableModels,
    bool? isTestingConnection,
    bool? connectionSuccess,
    String? error,
  }) {
    return SettingsState(
      backendUrl: backendUrl ?? this.backendUrl,
      apiKey: apiKey ?? this.apiKey,
      themeMode: themeMode ?? this.themeMode,
      locale: locale ?? this.locale,
      selectedModel: selectedModel ?? this.selectedModel,
      voiceInputEnabled: voiceInputEnabled ?? this.voiceInputEnabled,
      voiceOutputEnabled: voiceOutputEnabled ?? this.voiceOutputEnabled,
      notificationsEnabled: notificationsEnabled ?? this.notificationsEnabled,
      availableModels: availableModels ?? this.availableModels,
      isTestingConnection: isTestingConnection ?? this.isTestingConnection,
      connectionSuccess: connectionSuccess ?? this.connectionSuccess,
      error: error,
    );
  }
}

class SettingsNotifier extends StateNotifier<SettingsState> {
  SettingsNotifier() : super(const SettingsState());

  Future<void> loadSettings() async {
    final storage = LocalStorage.instance;
    final apiKey = await storage.apiKey ?? '';
    final models = await _loadModels();

    state = state.copyWith(
      backendUrl: storage.backendUrl,
      apiKey: apiKey,
      themeMode: storage.themeMode,
      locale: storage.locale,
      selectedModel: storage.selectedModel,
      availableModels: models,
    );
  }

  Future<List<String>> _loadModels() async {
    try {
      final modelsJson = await ApiClient.instance.getModels();
      return modelsJson.map((m) => m['name'] as String? ?? m['id'] as String? ?? '').where((n) => n.isNotEmpty).toList();
    } catch (_) {
      return [];
    }
  }

  Future<void> updateBackendUrl(String url) async {
    await LocalStorage.instance.setBackendUrl(url);
    ApiClient.instance.configure(baseUrl: url, apiKey: state.apiKey.isNotEmpty ? state.apiKey : null);
    state = state.copyWith(backendUrl: url, connectionSuccess: false, error: null);
  }

  Future<void> updateApiKey(String key) async {
    if (key.isNotEmpty) {
      await LocalStorage.instance.setApiKey(key);
    } else {
      await LocalStorage.instance.deleteApiKey();
    }
    ApiClient.instance.configure(baseUrl: state.backendUrl, apiKey: key.isNotEmpty ? key : null);
    state = state.copyWith(apiKey: key, connectionSuccess: false, error: null);
  }

  Future<void> updateThemeMode(String mode) async {
    await LocalStorage.instance.setThemeMode(mode);
    state = state.copyWith(themeMode: mode);
  }

  Future<void> updateLocale(String locale) async {
    await LocalStorage.instance.setLocale(locale);
    state = state.copyWith(locale: locale);
  }

  Future<void> updateModel(String model) async {
    await LocalStorage.instance.setSelectedModel(model);
    state = state.copyWith(selectedModel: model);
  }

  void updateVoiceInput(bool enabled) {
    LocalStorage.instance.setBool(AppConstants.voiceEnabledKey, enabled);
    state = state.copyWith(voiceInputEnabled: enabled);
  }

  void updateVoiceOutput(bool enabled) {
    LocalStorage.instance.setBool('voice_output_enabled', enabled);
    state = state.copyWith(voiceOutputEnabled: enabled);
  }

  void updateNotifications(bool enabled) {
    LocalStorage.instance.setBool(AppConstants.notificationsEnabledKey, enabled);
    state = state.copyWith(notificationsEnabled: enabled);
  }

  Future<void> testConnection() async {
    state = state.copyWith(isTestingConnection: true, error: null, connectionSuccess: false);
    try {
      final success = await ApiClient.instance.testConnection();
      state = state.copyWith(
        isTestingConnection: false,
        connectionSuccess: success,
      );
    } catch (e) {
      state = state.copyWith(
        isTestingConnection: false,
        connectionSuccess: false,
        error: e.toString(),
      );
    }
  }

  Future<void> refreshModels() async {
    final models = await _loadModels();
    state = state.copyWith(availableModels: models);
  }

  Future<void> logout() async {
    await LocalStorage.instance.setOnboardingComplete(false);
    await LocalStorage.instance.deleteApiKey();
    state = const SettingsState();
  }
}

final settingsProvider = StateNotifierProvider<SettingsNotifier, SettingsState>(
  (ref) => SettingsNotifier(),
);
