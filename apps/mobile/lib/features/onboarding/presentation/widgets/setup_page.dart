import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/theme/app_theme.dart';
import '../providers/onboarding_provider.dart';

class SetupPage extends ConsumerStatefulWidget {
  final VoidCallback onComplete;

  const SetupPage({super.key, required this.onComplete});

  @override
  ConsumerState<SetupPage> createState() => _SetupPageState();
}

class _SetupPageState extends ConsumerState<SetupPage> {
  final _urlController = TextEditingController();
  final _apiKeyController = TextEditingController();
  final _urlFocus = FocusNode();
  final _apiKeyFocus = FocusNode();
  bool _obscureApiKey = true;

  @override
  void initState() {
    super.initState();
    final state = ref.read(onboardingProvider);
    _urlController.text = state.backendUrl;
    _apiKeyController.text = state.apiKey;
  }

  @override
  void dispose() {
    _urlController.dispose();
    _apiKeyController.dispose();
    _urlFocus.dispose();
    _apiKeyFocus.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(onboardingProvider);
    final notifier = ref.read(onboardingProvider.notifier);

    return Container(
      decoration: const BoxDecoration(
        color: Color(0xFF0F0F1A),
      ),
      child: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const SizedBox(height: 24),

              // Header
              Container(
                width: 56,
                height: 56,
                decoration: BoxDecoration(
                  gradient: AppTheme.primaryGradient,
                  borderRadius: BorderRadius.circular(16),
                ),
                child: const Icon(Icons.settings_ethernet, color: Colors.white, size: 28),
              ),

              const SizedBox(height: 20),

              const Text(
                'إعداد الاتصال',
                style: TextStyle(
                  fontSize: 28,
                  fontWeight: FontWeight.w800,
                  color: Colors.white,
                ),
              ),

              const SizedBox(height: 8),

              const Text(
                'أدخل رابط الخادم ومفتاح API للاتصال بمساعدك الذكي',
                style: TextStyle(
                  fontSize: 15,
                  color: Color(0xFF6B6B8D),
                  height: 1.5,
                ),
              ),

              const SizedBox(height: 32),

              // Backend URL Field
              const Text(
                'رابط الخادم',
                style: TextStyle(
                  color: Colors.white,
                  fontWeight: FontWeight.w600,
                  fontSize: 14,
                ),
              ),
              const SizedBox(height: 8),
              TextField(
                controller: _urlController,
                focusNode: _urlFocus,
                onChanged: (value) => notifier.updateBackendUrl(value),
                style: const TextStyle(color: Colors.white, fontSize: 16),
                decoration: InputDecoration(
                  hintText: 'http://localhost:8000',
                  hintStyle: const TextStyle(color: Color(0xFF4A4A6A)),
                  prefixIcon: const Icon(Icons.cloud_outlined, color: Color(0xFF6C63FF)),
                  suffixIcon: _urlController.text.isNotEmpty
                      ? IconButton(
                          icon: const Icon(Icons.clear, color: Color(0xFF6B6B8D)),
                          onPressed: () {
                            _urlController.clear();
                            notifier.updateBackendUrl('');
                          },
                        )
                      : null,
                ),
                keyboardType: TextInputType.url,
                textDirection: TextDirection.ltr,
              ),

              const SizedBox(height: 20),

              // API Key Field
              const Text(
                'مفتاح API',
                style: TextStyle(
                  color: Colors.white,
                  fontWeight: FontWeight.w600,
                  fontSize: 14,
                ),
              ),
              const SizedBox(height: 8),
              TextField(
                controller: _apiKeyController,
                focusNode: _apiKeyFocus,
                onChanged: (value) => notifier.updateApiKey(value),
                obscureText: _obscureApiKey,
                style: const TextStyle(color: Colors.white, fontSize: 16),
                decoration: InputDecoration(
                  hintText: 'أدخل مفتاح API',
                  hintStyle: const TextStyle(color: Color(0xFF4A4A6A)),
                  prefixIcon: const Icon(Icons.key, color: Color(0xFF6C63FF)),
                  suffixIcon: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      IconButton(
                        icon: Icon(
                          _obscureApiKey ? Icons.visibility_off : Icons.visibility,
                          color: const Color(0xFF6B6B8D),
                        ),
                        onPressed: () {
                          setState(() {
                            _obscureApiKey = !_obscureApiKey;
                          });
                        },
                      ),
                      if (_apiKeyController.text.isNotEmpty)
                        IconButton(
                          icon: const Icon(Icons.clear, color: Color(0xFF6B6B8D)),
                          onPressed: () {
                            _apiKeyController.clear();
                            notifier.updateApiKey('');
                          },
                        ),
                    ],
                  ),
                ),
              ),

              const SizedBox(height: 8),

              // Info text
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: const Color(0xFF6C63FF).withValues(alpha: 0.08),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(
                    color: const Color(0xFF6C63FF).withValues(alpha: 0.2),
                  ),
                ),
                child: const Row(
                  children: [
                    Icon(Icons.info_outline, color: Color(0xFF6C63FF), size: 18),
                    SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        'مفتاح API اختياري لبعض الخوادم. يمكنك إضافته لاحقاً من الإعدادات.',
                        style: TextStyle(
                          color: Color(0xFF9E9EB8),
                          fontSize: 12,
                        ),
                      ),
                    ),
                  ],
                ),
              ),

              const SizedBox(height: 24),

              // Error Message
              if (state.errorMessage != null)
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: const Color(0xFFFF5252).withValues(alpha: 0.1),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(
                      color: const Color(0xFFFF5252).withValues(alpha: 0.3),
                    ),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.error_outline, color: Color(0xFFFF5252), size: 20),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          state.errorMessage!,
                          style: const TextStyle(
                            color: Color(0xFFFF5252),
                            fontSize: 13,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),

              // Connection Success
              if (state.connectionSuccess)
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: const Color(0xFF00E676).withValues(alpha: 0.1),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(
                      color: const Color(0xFF00E676).withValues(alpha: 0.3),
                    ),
                  ),
                  child: const Row(
                    children: [
                      Icon(Icons.check_circle, color: Color(0xFF00E676), size: 20),
                      SizedBox(width: 8),
                      Text(
                        'تم الاتصال بنجاح!',
                        style: TextStyle(
                          color: Color(0xFF00E676),
                          fontSize: 14,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ],
                  ),
                ),

              const Spacer(),

              // Test Connection Button
              SizedBox(
                width: double.infinity,
                height: 52,
                child: OutlinedButton(
                  onPressed: state.isTesting ? null : () async {
                    await notifier.testConnection();
                  },
                  style: OutlinedButton.styleFrom(
                    side: BorderSide(
                      color: const Color(0xFF6C63FF).withValues(alpha: 0.5),
                    ),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(14),
                    ),
                  ),
                  child: state.isTesting
                      ? const SizedBox(
                          width: 20,
                          height: 20,
                          child: CircularProgressIndicator(
                            strokeWidth: 2,
                            color: Color(0xFF6C63FF),
                          ),
                        )
                      : const Row(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(Icons.wifi_tethering, size: 20),
                            SizedBox(width: 8),
                            Text(
                              'اختبار الاتصال',
                              style: TextStyle(
                                fontSize: 16,
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                          ],
                        ),
                ),
              ),

              const SizedBox(height: 12),

              // Continue Button
              SizedBox(
                width: double.infinity,
                height: 52,
                child: ElevatedButton(
                  onPressed: state.backendUrl.isNotEmpty
                      ? () => notifier.goToStep(OnboardingStep.tutorial)
                      : null,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFF6C63FF),
                    foregroundColor: Colors.white,
                    disabledBackgroundColor: const Color(0xFF2A2A45),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(14),
                    ),
                  ),
                  child: const Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Text(
                        'التالي',
                        style: TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                      SizedBox(width: 8),
                      Icon(Icons.arrow_back, size: 18),
                    ],
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
}
