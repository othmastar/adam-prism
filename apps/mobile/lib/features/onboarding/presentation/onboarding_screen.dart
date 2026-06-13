import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../providers/onboarding_provider.dart';
import '../widgets/welcome_page.dart';
import '../widgets/setup_page.dart';
import '../widgets/tutorial_page.dart';

class OnboardingScreen extends ConsumerWidget {
  final VoidCallback onComplete;

  const OnboardingScreen({super.key, required this.onComplete});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(onboardingProvider);
    final notifier = ref.read(onboardingProvider.notifier);

    return Directionality(
      textDirection: TextDirection.rtl,
      child: Scaffold(
        body: AnimatedSwitcher(
          duration: const Duration(milliseconds: 400),
          switchInCurve: Curves.easeOutCubic,
          switchOutCurve: Curves.easeInCubic,
          child: _buildCurrentStep(state, notifier),
        ),
      ),
    );
  }

  Widget _buildCurrentStep(OnboardingState state, OnboardingNotifier notifier) {
    switch (state.step) {
      case OnboardingStep.welcome:
        return WelcomePage(
          key: const ValueKey('welcome'),
          onGetStarted: () => notifier.goToStep(OnboardingStep.setup),
        );
      case OnboardingStep.setup:
        return SetupPage(
          key: const ValueKey('setup'),
          onComplete: () => notifier.goToStep(OnboardingStep.tutorial),
        );
      case OnboardingStep.tutorial:
        return TutorialPage(
          key: const ValueKey('tutorial'),
          currentPage: state.tutorialPage,
          onNext: notifier.nextTutorialPage,
          onPrevious: notifier.previousTutorialPage,
          onComplete: () async {
            await notifier.completeOnboarding();
            onComplete();
          },
        );
      case OnboardingStep.complete:
        onComplete();
        return const SizedBox.shrink();
    }
  }
}
