import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/api/api_client.dart';
import '../../core/storage/local_storage.dart';
import '../../core/constants/app_constants.dart';

enum OnboardingStep { welcome, setup, tutorial, complete }

class OnboardingState {
  final OnboardingStep step;
  final String backendUrl;
  final String apiKey;
  final bool isTesting;
  final bool connectionSuccess;
  final String? errorMessage;
  final int tutorialPage;

  const OnboardingState({
    this.step = OnboardingStep.welcome,
    this.backendUrl = AppConstants.defaultBackendUrl,
    this.apiKey = '',
    this.isTesting = false,
    this.connectionSuccess = false,
    this.errorMessage,
    this.tutorialPage = 0,
  });

  OnboardingState copyWith({
    OnboardingStep? step,
    String? backendUrl,
    String? apiKey,
    bool? isTesting,
    bool? connectionSuccess,
    String? errorMessage,
    int? tutorialPage,
  }) {
    return OnboardingState(
      step: step ?? this.step,
      backendUrl: backendUrl ?? this.backendUrl,
      apiKey: apiKey ?? this.apiKey,
      isTesting: isTesting ?? this.isTesting,
      connectionSuccess: connectionSuccess ?? this.connectionSuccess,
      errorMessage: errorMessage,
      tutorialPage: tutorialPage ?? this.tutorialPage,
    );
  }
}

class OnboardingNotifier extends StateNotifier<OnboardingState> {
  OnboardingNotifier() : super(const OnboardingState());

  void goToStep(OnboardingStep step) {
    state = state.copyWith(step: step);
  }

  void updateBackendUrl(String url) {
    state = state.copyWith(backendUrl: url, errorMessage: null);
  }

  void updateApiKey(String key) {
    state = state.copyWith(apiKey: key, errorMessage: null);
  }

  Future<void> testConnection() async {
    state = state.copyWith(isTesting: true, errorMessage: null, connectionSuccess: false);

    try {
      ApiClient.instance.configure(
        baseUrl: state.backendUrl,
        apiKey: state.apiKey.isNotEmpty ? state.apiKey : null,
      );

      final success = await ApiClient.instance.testConnection();

      if (success) {
        state = state.copyWith(isTesting: false, connectionSuccess: true);
      } else {
        state = state.copyWith(
          isTesting: false,
          connectionSuccess: false,
          errorMessage: 'فشل الاتصال بالخادم',
        );
      }
    } catch (e) {
      state = state.copyWith(
        isTesting: false,
        connectionSuccess: false,
        errorMessage: e.toString(),
      );
    }
  }

  Future<void> completeOnboarding() async {
    await LocalStorage.instance.setOnboardingComplete(true);
    await LocalStorage.instance.setBackendUrl(state.backendUrl);
    if (state.apiKey.isNotEmpty) {
      await LocalStorage.instance.setApiKey(state.apiKey);
    }
    ApiClient.instance.configure(
      baseUrl: state.backendUrl,
      apiKey: state.apiKey.isNotEmpty ? state.apiKey : null,
    );
    state = state.copyWith(step: OnboardingStep.complete);
  }

  void nextTutorialPage() {
    state = state.copyWith(tutorialPage: state.tutorialPage + 1);
  }

  void previousTutorialPage() {
    if (state.tutorialPage > 0) {
      state = state.copyWith(tutorialPage: state.tutorialPage - 1);
    }
  }
}

final onboardingProvider =
    StateNotifierProvider<OnboardingNotifier, OnboardingState>(
  (ref) => OnboardingNotifier(),
);
