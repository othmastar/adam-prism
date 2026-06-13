import 'package:flutter/material.dart';
import '../../../core/theme/app_theme.dart';

class TutorialPage extends StatelessWidget {
  final int currentPage;
  final VoidCallback onNext;
  final VoidCallback onPrevious;
  final VoidCallback onComplete;

  const TutorialPage({
    super.key,
    required this.currentPage,
    required this.onNext,
    required this.onPrevious,
    required this.onComplete,
  });

  static const _tutorials = [
    _TutorialData(
      icon: Icons.waving_hand,
      title: 'مرحباً بك في آدم بريزم',
      description: 'مساعدك الذكي الشخصي الذي يتعلم ويتذكر. اسألني أي شيء وسأساعدك!',
      gradient: [Color(0xFF6C63FF), Color(0xFF8B7FFF)],
    ),
    _TutorialData(
      icon: Icons.record_voice_over,
      title: 'تحدث بشكل طبيعي',
      description: 'استخدم الصوت أو النص للتواصل. يمكنك استخدام أوامر خاصة مثل /new و /help للتحكم السريع.',
      gradient: [Color(0xFF00D9FF), Color(0xFF00B8D9)],
    ),
    _TutorialData(
      icon: Icons.psychology,
      title: 'الذكاء الذي يتذكر',
      description: 'آدم يتذكر محادثاتك ويبني معرفته. كلما تحدثت أكثر، أصبح أكثر ذكاءً في مساعدتك.',
      gradient: [Color(0xFF00E676), Color(0xFF00C853)],
    ),
  ];

  @override
  Widget build(BuildContext context) {
    final tutorial = _tutorials[currentPage];
    final isLast = currentPage == _tutorials.length - 1;

    return Container(
      decoration: const BoxDecoration(
        color: Color(0xFF0F0F1A),
      ),
      child: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 32),
          child: Column(
            children: [
              const SizedBox(height: 16),

              // Skip button
              Align(
                alignment: AlignmentDirectional.topEnd,
                child: TextButton(
                  onPressed: onComplete,
                  child: const Text(
                    'تخطي',
                    style: TextStyle(
                      color: Color(0xFF6B6B8D),
                      fontSize: 15,
                    ),
                  ),
                ),
              ),

              const Spacer(flex: 2),

              // Illustration
              Container(
                width: 180,
                height: 180,
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    colors: tutorial.gradient,
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                  ),
                  borderRadius: BorderRadius.circular(48),
                  boxShadow: [
                    BoxShadow(
                      color: tutorial.gradient[0].withValues(alpha: 0.3),
                      blurRadius: 40,
                      spreadRadius: 4,
                    ),
                  ],
                ),
                child: Center(
                  child: Icon(
                    tutorial.icon,
                    size: 80,
                    color: Colors.white,
                  ),
                ),
              ),

              const Spacer(flex: 2),

              // Title
              Text(
                tutorial.title,
                style: const TextStyle(
                  fontSize: 26,
                  fontWeight: FontWeight.w800,
                  color: Colors.white,
                  height: 1.3,
                ),
                textAlign: TextAlign.center,
              ),

              const SizedBox(height: 16),

              // Description
              Text(
                tutorial.description,
                style: const TextStyle(
                  fontSize: 16,
                  color: Color(0xFF9E9EB8),
                  height: 1.7,
                ),
                textAlign: TextAlign.center,
              ),

              const Spacer(flex: 2),

              // Page indicators
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: List.generate(_tutorials.length, (index) {
                  return AnimatedContainer(
                    duration: const Duration(milliseconds: 300),
                    margin: const EdgeInsets.symmetric(horizontal: 4),
                    width: currentPage == index ? 32 : 8,
                    height: 8,
                    decoration: BoxDecoration(
                      color: currentPage == index
                          ? tutorial.gradient[0]
                          : const Color(0xFF2A2A45),
                      borderRadius: BorderRadius.circular(4),
                    ),
                  );
                }),
              ),

              const SizedBox(height: 32),

              // Navigation Buttons
              Row(
                children: [
                  if (currentPage > 0)
                    Expanded(
                      child: OutlinedButton(
                        onPressed: onPrevious,
                        style: OutlinedButton.styleFrom(
                          side: const BorderSide(color: Color(0xFF2A2A45)),
                          padding: const EdgeInsets.symmetric(vertical: 16),
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(14),
                          ),
                        ),
                        child: const Text(
                          'رجوع',
                          style: TextStyle(fontWeight: FontWeight.w600),
                        ),
                      ),
                    ),
                  if (currentPage > 0) const SizedBox(width: 12),
                  Expanded(
                    flex: currentPage > 0 ? 2 : 1,
                    child: ElevatedButton(
                      onPressed: isLast ? onComplete : onNext,
                      style: ElevatedButton.styleFrom(
                        backgroundColor: tutorial.gradient[0],
                        foregroundColor: Colors.white,
                        padding: const EdgeInsets.symmetric(vertical: 16),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(14),
                        ),
                      ),
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Text(
                            isLast ? 'ابدأ المحادثة' : 'التالي',
                            style: const TextStyle(
                              fontSize: 16,
                              fontWeight: FontWeight.w700,
                            ),
                          ),
                          const SizedBox(width: 8),
                          Icon(
                            isLast ? Icons.chat_bubble : Icons.arrow_back,
                            size: 18,
                          ),
                        ],
                      ),
                    ),
                  ),
                ],
              ),

              const SizedBox(height: 32),
            ],
          ),
        ),
      ),
    );
  }
}

class _TutorialData {
  final IconData icon;
  final String title;
  final String description;
  final List<Color> gradient;

  const _TutorialData({
    required this.icon,
    required this.title,
    required this.description,
    required this.gradient,
  });
}
