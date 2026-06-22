import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/theme/app_theme.dart';
import '../../../core/utils/helpers.dart';
import '../providers/settings_provider.dart';

class SettingsScreen extends ConsumerStatefulWidget {
  const SettingsScreen({super.key});

  @override
  ConsumerState<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends ConsumerState<SettingsScreen> {
  final _urlController = TextEditingController();
  final _apiKeyController = TextEditingController();
  bool _obscureApiKey = true;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      ref.read(settingsProvider.notifier).loadSettings();
    });
  }

  @override
  void dispose() {
    _urlController.dispose();
    _apiKeyController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(settingsProvider);

    // Sync controllers
    if (_urlController.text != state.backendUrl) {
      _urlController.text = state.backendUrl;
    }
    if (_apiKeyController.text != state.apiKey) {
      _apiKeyController.text = state.apiKey;
    }

    return Container(
      decoration: const BoxDecoration(color: Color(0xFF0F0F1A)),
      child: Column(
        children: [
          // Header
          Container(
            padding: const EdgeInsets.fromLTRB(20, 16, 20, 16),
            decoration: const BoxDecoration(
              color: Color(0xFF1A1A2E),
              border: Border(
                bottom: BorderSide(color: Color(0xFF2A2A45), width: 0.5),
              ),
            ),
            child: SafeArea(
              bottom: false,
              child: Row(
                children: [
                  const Text(
                    'الإعدادات',
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 24,
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                  const Spacer(),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                    decoration: BoxDecoration(
                      color: state.connectionSuccess
                          ? const Color(0xFF00E676).withValues(alpha: 0.1)
                          : const Color(0xFF2A2A45),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(
                          state.connectionSuccess ? Icons.cloud_done : Icons.cloud_off,
                          color: state.connectionSuccess
                              ? const Color(0xFF00E676)
                              : const Color(0xFF6B6B8D),
                          size: 14,
                        ),
                        const SizedBox(width: 6),
                        Text(
                          state.connectionSuccess ? 'متصل' : 'غير متصل',
                          style: TextStyle(
                            color: state.connectionSuccess
                                ? const Color(0xFF00E676)
                                : const Color(0xFF6B6B8D),
                            fontSize: 12,
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),

          // Settings list
          Expanded(
            child: ListView(
              padding: const EdgeInsets.symmetric(vertical: 16),
              children: [
                // Connection section
                _buildSectionHeader('الاتصال'),
                _buildTextField(
                  controller: _urlController,
                  label: 'رابط الخادم',
                  icon: Icons.cloud_outlined,
                  onChanged: (v) => ref.read(settingsProvider.notifier).updateBackendUrl(v),
                ),
                _buildApiKeyField(state),
                _buildTestConnectionButton(state),

                const SizedBox(height: 24),

                // Appearance section
                _buildSectionHeader('المظهر'),
                _buildThemeSelector(state),
                _buildLanguageSelector(state),

                const SizedBox(height: 24),

                // Model section
                _buildSectionHeader('النموذج'),
                _buildModelSelector(state),

                const SizedBox(height: 24),

                // Voice section
                _buildSectionHeader('الصوت'),
                _buildSwitchTile(
                  title: 'الإدخال الصوتي',
                  subtitle: 'تفعيل التعرف على الكلام',
                  icon: Icons.mic,
                  value: state.voiceInputEnabled,
                  onChanged: (v) => ref.read(settingsProvider.notifier).updateVoiceInput(v),
                ),
                _buildSwitchTile(
                  title: 'الإخراج الصوتي',
                  subtitle: 'تفعيل تحويل النص إلى كلام',
                  icon: Icons.volume_up,
                  value: state.voiceOutputEnabled,
                  onChanged: (v) => ref.read(settingsProvider.notifier).updateVoiceOutput(v),
                ),

                const SizedBox(height: 24),

                // Notifications
                _buildSectionHeader('الإشعارات'),
                _buildSwitchTile(
                  title: 'تفعيل الإشعارات',
                  subtitle: 'استقبال إشعارات من المساعد',
                  icon: Icons.notifications,
                  value: state.notificationsEnabled,
                  onChanged: (v) => ref.read(settingsProvider.notifier).updateNotifications(v),
                ),

                const SizedBox(height: 24),

                // About
                _buildSectionHeader('حول'),
                _buildInfoTile(
                  title: 'آدم بريزم',
                  subtitle: 'الإصدار 1.0.0',
                  icon: Icons.info_outline,
                ),

                const SizedBox(height: 16),

                // Logout
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 16),
                  child: OutlinedButton(
                    onPressed: () => _showLogoutDialog(),
                    style: OutlinedButton.styleFrom(
                      foregroundColor: const Color(0xFFFF5252),
                      side: const BorderSide(color: Color(0xFFFF5252), width: 0.5),
                      padding: const EdgeInsets.symmetric(vertical: 14),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(14),
                      ),
                    ),
                    child: const Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(Icons.logout, size: 18),
                        SizedBox(width: 8),
                        Text('تسجيل الخروج', style: TextStyle(fontWeight: FontWeight.w600)),
                      ],
                    ),
                  ),
                ),

                const SizedBox(height: 40),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSectionHeader(String title) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(20, 8, 20, 12),
      child: Text(
        title,
        style: const TextStyle(
          color: Color(0xFF6C63FF),
          fontSize: 13,
          fontWeight: FontWeight.w700,
          letterSpacing: 0.5,
        ),
      ),
    );
  }

  Widget _buildTextField({
    required TextEditingController controller,
    required String label,
    required IconData icon,
    required Function(String) onChanged,
  }) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
      child: TextField(
        controller: controller,
        onChanged: onChanged,
        style: const TextStyle(color: Colors.white, fontSize: 14),
        textDirection: TextDirection.ltr,
        decoration: InputDecoration(
          labelText: label,
          labelStyle: const TextStyle(color: Color(0xFF6B6B8D)),
          prefixIcon: Icon(icon, color: const Color(0xFF6C63FF), size: 20),
        ),
      ),
    );
  }

  Widget _buildApiKeyField(SettingsState state) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
      child: TextField(
        controller: _apiKeyController,
        obscureText: _obscureApiKey,
        onChanged: (v) => ref.read(settingsProvider.notifier).updateApiKey(v),
        style: const TextStyle(color: Colors.white, fontSize: 14),
        textDirection: TextDirection.ltr,
        decoration: InputDecoration(
          labelText: 'مفتاح API',
          labelStyle: const TextStyle(color: Color(0xFF6B6B8D)),
          prefixIcon: const Icon(Icons.key, color: Color(0xFF6C63FF), size: 20),
          suffixIcon: IconButton(
            icon: Icon(
              _obscureApiKey ? Icons.visibility_off : Icons.visibility,
              color: const Color(0xFF6B6B8D),
              size: 20,
            ),
            onPressed: () => setState(() => _obscureApiKey = !_obscureApiKey),
          ),
        ),
      ),
    );
  }

  Widget _buildTestConnectionButton(SettingsState state) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: SizedBox(
        width: double.infinity,
        height: 46,
        child: OutlinedButton(
          onPressed: state.isTestingConnection
              ? null
              : () => ref.read(settingsProvider.notifier).testConnection(),
          style: OutlinedButton.styleFrom(
            side: BorderSide(
              color: state.connectionSuccess
                  ? const Color(0xFF00E676)
                  : const Color(0xFF6C63FF).withValues(alpha: 0.5),
            ),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(14),
            ),
          ),
          child: state.isTestingConnection
              ? const SizedBox(
                  width: 18,
                  height: 18,
                  child: CircularProgressIndicator(strokeWidth: 2, color: Color(0xFF6C63FF)),
                )
              : Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(
                      state.connectionSuccess ? Icons.check_circle : Icons.wifi_tethering,
                      size: 18,
                      color: state.connectionSuccess ? const Color(0xFF00E676) : const Color(0xFF6C63FF),
                    ),
                    const SizedBox(width: 8),
                    Text(
                      state.connectionSuccess ? 'تم الاتصال بنجاح!' : 'اختبار الاتصال',
                      style: TextStyle(
                        fontWeight: FontWeight.w600,
                        color: state.connectionSuccess ? const Color(0xFF00E676) : const Color(0xFF6C63FF),
                      ),
                    ),
                  ],
                ),
        ),
      ),
    );
  }

  Widget _buildThemeSelector(SettingsState state) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
      child: Container(
        padding: const EdgeInsets.all(4),
        decoration: BoxDecoration(
          color: const Color(0xFF1E1E32),
          borderRadius: BorderRadius.circular(14),
        ),
        child: Row(
          children: [
            _ThemeOption(
              label: 'داكن',
              icon: Icons.dark_mode,
              isSelected: state.themeMode == 'dark',
              onTap: () => ref.read(settingsProvider.notifier).updateThemeMode('dark'),
            ),
            _ThemeOption(
              label: 'فاتح',
              icon: Icons.light_mode,
              isSelected: state.themeMode == 'light',
              onTap: () => ref.read(settingsProvider.notifier).updateThemeMode('light'),
            ),
            _ThemeOption(
              label: 'تلقائي',
              icon: Icons.brightness_auto,
              isSelected: state.themeMode == 'system',
              onTap: () => ref.read(settingsProvider.notifier).updateThemeMode('system'),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildLanguageSelector(SettingsState state) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
      child: Container(
        padding: const EdgeInsets.all(4),
        decoration: BoxDecoration(
          color: const Color(0xFF1E1E32),
          borderRadius: BorderRadius.circular(14),
        ),
        child: Row(
          children: [
            _ThemeOption(
              label: 'العربية',
              icon: Icons.translate,
              isSelected: state.locale == 'ar',
              onTap: () => ref.read(settingsProvider.notifier).updateLocale('ar'),
            ),
            _ThemeOption(
              label: 'English',
              icon: Icons.language,
              isSelected: state.locale == 'en',
              onTap: () => ref.read(settingsProvider.notifier).updateLocale('en'),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildModelSelector(SettingsState state) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 4),
        decoration: BoxDecoration(
          color: const Color(0xFF1E1E32),
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: const Color(0xFF2A2A45), width: 0.5),
        ),
        child: DropdownButtonHideUnderline(
          child: DropdownButton<String>(
            value: state.selectedModel.isNotEmpty ? state.selectedModel : null,
            hint: const Text('اختر النموذج', style: TextStyle(color: Color(0xFF6B6B8D), fontSize: 14)),
            icon: const Icon(Icons.expand_more, color: Color(0xFF6B6B8D)),
            isExpanded: true,
            dropdownColor: const Color(0xFF1E1E32),
            style: const TextStyle(color: Colors.white, fontSize: 14),
            items: [
              ...state.availableModels.map((model) => DropdownMenuItem(
                value: model,
                child: Text(model, style: const TextStyle(color: Colors.white)),
              )),
              if (state.availableModels.isEmpty)
                const DropdownMenuItem(
                  value: null,
                  enabled: false,
                  child: Text('لا توجد نماذج', style: TextStyle(color: Color(0xFF6B6B8D))),
                ),
            ],
            onChanged: (value) {
              if (value != null) {
                ref.read(settingsProvider.notifier).updateModel(value);
              }
            },
          ),
        ),
      ),
    );
  }

  Widget _buildSwitchTile({
    required String title,
    required String subtitle,
    required IconData icon,
    required bool value,
    required Function(bool) onChanged,
  }) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
      child: Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: const Color(0xFF1E1E32),
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: const Color(0xFF2A2A45), width: 0.5),
        ),
        child: Row(
          children: [
            Container(
              width: 38,
              height: 38,
              decoration: BoxDecoration(
                color: const Color(0xFF6C63FF).withValues(alpha: 0.1),
                borderRadius: BorderRadius.circular(10),
              ),
              child: Icon(icon, color: const Color(0xFF6C63FF), size: 18),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    title,
                    style: const TextStyle(color: Colors.white, fontSize: 14, fontWeight: FontWeight.w600),
                  ),
                  Text(
                    subtitle,
                    style: const TextStyle(color: Color(0xFF6B6B8D), fontSize: 12),
                  ),
                ],
              ),
            ),
            Switch(
              value: value,
              onChanged: onChanged,
              activeColor: const Color(0xFF6C63FF),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildInfoTile({
    required String title,
    required String subtitle,
    required IconData icon,
  }) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
      child: Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: const Color(0xFF1E1E32),
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: const Color(0xFF2A2A45), width: 0.5),
        ),
        child: Row(
          children: [
            Container(
              width: 38,
              height: 38,
              decoration: BoxDecoration(
                color: const Color(0xFF6C63FF).withValues(alpha: 0.1),
                borderRadius: BorderRadius.circular(10),
              ),
              child: Icon(icon, color: const Color(0xFF6C63FF), size: 18),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    title,
                    style: const TextStyle(color: Colors.white, fontSize: 14, fontWeight: FontWeight.w600),
                  ),
                  Text(
                    subtitle,
                    style: const TextStyle(color: Color(0xFF6B6B8D), fontSize: 12),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  void _showLogoutDialog() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: const Color(0xFF1E1E32),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        title: const Text('تسجيل الخروج', style: TextStyle(color: Colors.white)),
        content: const Text(
          'هل تريد تسجيل الخروج؟ سيتم حذف بيانات الاتصال.',
          style: TextStyle(color: Color(0xFF9E9EB8)),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('إلغاء'),
          ),
          TextButton(
            onPressed: () {
              ref.read(settingsProvider.notifier).logout();
              Navigator.pop(context);
            },
            child: const Text('خروج', style: TextStyle(color: Color(0xFFFF5252))),
          ),
        ],
      ),
    );
  }
}

class _ThemeOption extends StatelessWidget {
  final String label;
  final IconData icon;
  final bool isSelected;
  final VoidCallback onTap;

  const _ThemeOption({
    required this.label,
    required this.icon,
    required this.isSelected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: GestureDetector(
        onTap: onTap,
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 200),
          padding: const EdgeInsets.symmetric(vertical: 10),
          decoration: BoxDecoration(
            color: isSelected
                ? const Color(0xFF6C63FF).withValues(alpha: 0.2)
                : Colors.transparent,
            borderRadius: BorderRadius.circular(10),
          ),
          child: Column(
            children: [
              Icon(
                icon,
                color: isSelected ? const Color(0xFF6C63FF) : const Color(0xFF6B6B8D),
                size: 20,
              ),
              const SizedBox(height: 4),
              Text(
                label,
                style: TextStyle(
                  color: isSelected ? const Color(0xFF6C63FF) : const Color(0xFF6B6B8D),
                  fontSize: 12,
                  fontWeight: isSelected ? FontWeight.w600 : FontWeight.w400,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
