import 'package:flutter/material.dart';
import '../../../core/theme/app_theme.dart';

class WelcomePage extends StatelessWidget {
  final VoidCallback onGetStarted;

  const WelcomePage({super.key, required this.onGetStarted});

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
          colors: [
            const Color(0xFF0F0F1A),
            const Color(0xFF1A1A2E).withValues(alpha: 0.8),
            const Color(0xFF6C63FF).withValues(alpha: 0.15),
          ],
        ),
      ),
      child: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 32),
          child: Column(
            children: [
              const Spacer(flex: 2),

              // Logo
              Container(
                width: 120,
                height: 120,
                decoration: BoxDecoration(
                  gradient: AppTheme.primaryGradient,
                  borderRadius: BorderRadius.circular(32),
                  boxShadow: [
                    BoxShadow(
                      color: const Color(0xFF6C63FF).withValues(alpha: 0.4),
                      blurRadius: 40,
                      spreadRadius: 8,
                    ),
                  ],
                ),
                child: Center(
                  child: ShaderMask(
                    shaderCallback: (bounds) => AppTheme.primaryGradient.createShader(bounds),
                    child: const Icon(
                      Icons.auto_awesome,
                      size: 56,
                      color: Colors.white,
                    ),
                  ),
                ),
              ),

              const SizedBox(height: 32),

              // App Name
              ShaderMask(
                shaderCallback: (bounds) => AppTheme.primaryGradient.createShader(bounds),
                child: const Text(
                  'آدم بريزم',
                  style: TextStyle(
                    fontSize: 42,
                    fontWeight: FontWeight.w800,
                    color: Colors.white,
                    letterSpacing: -1,
                  ),
                  textAlign: TextAlign.center,
                ),
              ),

              const SizedBox(height: 8),

              const Text(
                'Adam Prism',
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.w300,
                  color: Color(0xFF6B6B8D),
                  letterSpacing: 4,
                ),
              ),

              const SizedBox(height: 24),

              // Tagline
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
                decoration: BoxDecoration(
                  color: const Color(0xFF6C63FF).withValues(alpha: 0.1),
                  borderRadius: BorderRadius.circular(20),
                  border: Border.all(
                    color: const Color(0xFF6C63FF).withValues(alpha: 0.3),
                  ),
                ),
                child: const Text(
                  'مساعدك الذكي الشخصي',
                  style: TextStyle(
                    fontSize: 16,
                    color: Color(0xFF00D9FF),
                    fontWeight: FontWeight.w500,
                  ),
                ),
              ),

              const Spacer(flex: 2),

              // Feature highlights
              _buildFeatureItem(
                Icons.psychology,
                'ذكاء اصطناعي متقدم',
                'يستخدم أحدث النماذج اللغوية',
              ),
              const SizedBox(height: 16),
              _buildFeatureItem(
                Icons.record_voice_over,
                'محادثة صوتية',
                'تحدث بشكل طبيعي مع المساعد',
              ),
              const SizedBox(height: 16),
              _buildFeatureItem(
                Icons.auto_stories,
                'ذاكرة ذكية',
                'يتذكر محادثاتك ويتعلم منها',
              ),

              const Spacer(flex: 2),

              // Get Started Button
              SizedBox(
                width: double.infinity,
                height: 56,
                child: ElevatedButton(
                  onPressed: onGetStarted,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFF6C63FF),
                    foregroundColor: Colors.white,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(16),
                    ),
                    elevation: 0,
                  ),
                  child: const Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Text(
                        'ابدأ الآن',
                        style: TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                      SizedBox(width: 8),
                      Icon(Icons.arrow_back, size: 20),
                    ],
                  ),
                ),
              ),

              const SizedBox(height: 16),

              // Skip option
              TextButton(
                onPressed: onGetStarted,
                child: const Text(
                  'تخطي الإعداد',
                  style: TextStyle(
                    color: Color(0xFF6B6B8D),
                    fontSize: 14,
                  ),
                ),
              ),

              const SizedBox(height: 32),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildFeatureItem(IconData icon, String title, String subtitle) {
    return Row(
      children: [
        Container(
          width: 44,
          height: 44,
          decoration: BoxDecoration(
            color: const Color(0xFF6C63FF).withValues(alpha: 0.15),
            borderRadius: BorderRadius.circular(12),
          ),
          child: Icon(icon, color: const Color(0xFF6C63FF), size: 22),
        ),
        const SizedBox(width: 16),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                title,
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 15,
                  fontWeight: FontWeight.w600,
                ),
              ),
              Text(
                subtitle,
                style: const TextStyle(
                  color: Color(0xFF6B6B8D),
                  fontSize: 13,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}
