import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'core/theme/app_theme.dart';
import 'core/storage/local_storage.dart';
import 'core/api/api_client.dart';
import 'core/constants/app_constants.dart';
import 'features/onboarding/presentation/onboarding_screen.dart';
import 'features/chat/presentation/chat_screen.dart';
import 'features/sessions/presentation/sessions_screen.dart';
import 'features/knowledge/presentation/knowledge_screen.dart';
import 'features/memory/presentation/memory_screen.dart';
import 'features/tools/presentation/tools_screen.dart';
import 'features/settings/presentation/settings_screen.dart';
import 'features/settings/providers/settings_provider.dart';

class AdamPrismApp extends ConsumerStatefulWidget {
  const AdamPrismApp({super.key});

  @override
  ConsumerState<AdamPrismApp> createState() => _AdamPrismAppState();
}

class _AdamPrismAppState extends ConsumerState<AdamPrismApp> {
  bool _initialized = false;
  bool _showOnboarding = false;

  @override
  void initState() {
    super.initState();
    _initApp();
  }

  Future<void> _initApp() async {
    await LocalStorage.instance.init();
    await ApiClient.instance.loadConfig();

    final isOnboarded = LocalStorage.instance.isOnboardingComplete;

    setState(() {
      _showOnboarding = !isOnboarded;
      _initialized = true;
    });

    if (isOnboarded) {
      ref.read(settingsProvider.notifier).loadSettings();
    }
  }

  @override
  Widget build(BuildContext context) {
    if (!_initialized) {
      return MaterialApp(
        debugShowCheckedModeBanner: false,
        home: Scaffold(
          backgroundColor: const Color(0xFF0F0F1A),
          body: Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Container(
                  width: 80,
                  height: 80,
                  decoration: BoxDecoration(
                    gradient: AppTheme.primaryGradient,
                    borderRadius: BorderRadius.circular(24),
                    boxShadow: [
                      BoxShadow(
                        color: const Color(0xFF6C63FF).withValues(alpha: 0.4),
                        blurRadius: 30,
                      ),
                    ],
                  ),
                  child: const Icon(
                    Icons.auto_awesome,
                    color: Colors.white,
                    size: 40,
                  ),
                ),
                const SizedBox(height: 24),
                ShaderMask(
                  shaderCallback: (bounds) => AppTheme.primaryGradient.createShader(bounds),
                  child: const Text(
                    'آدم بريزم',
                    style: TextStyle(
                      fontSize: 28,
                      fontWeight: FontWeight.w800,
                      color: Colors.white,
                    ),
                  ),
                ),
                const SizedBox(height: 20),
                const CircularProgressIndicator(
                  color: Color(0xFF6C63FF),
                  strokeWidth: 2,
                ),
              ],
            ),
          ),
        ),
      );
    }

    final settingsState = ref.watch(settingsProvider);
    final locale = settingsState.locale == 'ar'
        ? const Locale('ar')
        : const Locale('en');

    final themeMode = settingsState.themeMode == 'dark'
        ? ThemeMode.dark
        : settingsState.themeMode == 'light'
            ? ThemeMode.light
            : ThemeMode.system;

    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'Adam Prism',
      theme: AppTheme.lightTheme,
      darkTheme: AppTheme.darkTheme,
      themeMode: themeMode,
      locale: locale,
      supportedLocales: const [
        Locale('ar'),
        Locale('en'),
      ],
      localizationsDelegates: const [
        GlobalMaterialLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
      ],
      home: _showOnboarding
          ? OnboardingScreen(
              onComplete: () {
                setState(() => _showOnboarding = false);
                ref.read(settingsProvider.notifier).loadSettings();
              },
            )
          : const _MainShell(),
    );
  }
}

class _MainShell extends ConsumerStatefulWidget {
  const _MainShell();

  @override
  ConsumerState<_MainShell> createState() => _MainShellState();
}

class _MainShellState extends ConsumerState<_MainShell> {
  int _currentIndex = 0;
  final _screens = const [
    ChatScreen(),
    SessionsScreen(),
    KnowledgeScreen(),
    MemoryScreen(),
    ToolsScreen(),
  ];

  @override
  Widget build(BuildContext context) {
    final width = MediaQuery.of(context).size.width;
    final isRTL = Directionality.of(context) == TextDirection.rtl;
    final settingsState = ref.watch(settingsProvider);
    final isPhone = width < AppConstants.phoneBreakpoint;
    final isTablet = width >= AppConstants.phoneBreakpoint && width < AppConstants.desktopBreakpoint;

    if (isPhone) {
      return _buildPhoneLayout(isRTL, settingsState);
    } else if (isTablet) {
      return _buildTabletLayout(isRTL, settingsState);
    } else {
      return _buildDesktopLayout(isRTL, settingsState);
    }
  }

  Widget _buildPhoneLayout(bool isRTL, SettingsState settingsState) {
    return Directionality(
      textDirection: settingsState.locale == 'ar' ? TextDirection.rtl : TextDirection.ltr,
      child: Scaffold(
        body: IndexedStack(
          index: _currentIndex,
          children: _screens,
        ),
        bottomNavigationBar: Container(
          decoration: BoxDecoration(
            color: const Color(0xFF1A1A2E),
            border: Border(
              top: BorderSide(
                color: const Color(0xFF2A2A45),
                width: 0.5,
              ),
            ),
          ),
          child: SafeArea(
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceAround,
                children: [
                  _NavItem(
                    icon: Icons.chat,
                    label: 'محادثة',
                    isSelected: _currentIndex == 0,
                    onTap: () => setState(() => _currentIndex = 0),
                  ),
                  _NavItem(
                    icon: Icons.history,
                    label: 'المحادثات',
                    isSelected: _currentIndex == 1,
                    onTap: () => setState(() => _currentIndex = 1),
                  ),
                  _NavItem(
                    icon: Icons.auto_stories,
                    label: 'المعرفة',
                    isSelected: _currentIndex == 2,
                    onTap: () => setState(() => _currentIndex = 2),
                  ),
                  _NavItem(
                    icon: Icons.psychology,
                    label: 'الذاكرة',
                    isSelected: _currentIndex == 3,
                    onTap: () => setState(() => _currentIndex = 3),
                  ),
                  _NavItem(
                    icon: Icons.build,
                    label: 'الأدوات',
                    isSelected: _currentIndex == 4,
                    onTap: () => setState(() => _currentIndex = 4),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildTabletLayout(bool isRTL, SettingsState settingsState) {
    return Directionality(
      textDirection: settingsState.locale == 'ar' ? TextDirection.rtl : TextDirection.ltr,
      child: Scaffold(
        body: Row(
          children: [
            // Side navigation
            Container(
              width: 80,
              decoration: BoxDecoration(
                color: const Color(0xFF1A1A2E),
                border: Border(
                  end: BorderSide(
                    color: const Color(0xFF2A2A45),
                    width: 0.5,
                  ),
                ),
              ),
              child: SafeArea(
                child: Column(
                  children: [
                    const SizedBox(height: 16),
                    // Logo
                    Container(
                      width: 44,
                      height: 44,
                      decoration: BoxDecoration(
                        gradient: AppTheme.primaryGradient,
                        borderRadius: BorderRadius.circular(14),
                      ),
                      child: const Icon(Icons.auto_awesome, color: Colors.white, size: 22),
                    ),
                    const SizedBox(height: 24),
                    _SideNavItem(
                      icon: Icons.chat,
                      label: 'محادثة',
                      isSelected: _currentIndex == 0,
                      onTap: () => setState(() => _currentIndex = 0),
                    ),
                    _SideNavItem(
                      icon: Icons.history,
                      label: 'المحادثات',
                      isSelected: _currentIndex == 1,
                      onTap: () => setState(() => _currentIndex = 1),
                    ),
                    _SideNavItem(
                      icon: Icons.auto_stories,
                      label: 'المعرفة',
                      isSelected: _currentIndex == 2,
                      onTap: () => setState(() => _currentIndex = 2),
                    ),
                    _SideNavItem(
                      icon: Icons.psychology,
                      label: 'الذاكرة',
                      isSelected: _currentIndex == 3,
                      onTap: () => setState(() => _currentIndex = 3),
                    ),
                    _SideNavItem(
                      icon: Icons.build,
                      label: 'الأدوات',
                      isSelected: _currentIndex == 4,
                      onTap: () => setState(() => _currentIndex = 4),
                    ),
                    const Spacer(),
                    _SideNavItem(
                      icon: Icons.settings,
                      label: 'الإعدادات',
                      isSelected: false,
                      onTap: () => _navigateToSettings(),
                    ),
                    const SizedBox(height: 16),
                  ],
                ),
              ),
            ),

            // Main content
            Expanded(
              child: IndexedStack(
                index: _currentIndex,
                children: _screens,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildDesktopLayout(bool isRTL, SettingsState settingsState) {
    return Directionality(
      textDirection: settingsState.locale == 'ar' ? TextDirection.rtl : TextDirection.ltr,
      child: Scaffold(
        body: Row(
          children: [
            // Side navigation - wider for desktop
            Container(
              width: 220,
              decoration: BoxDecoration(
                color: const Color(0xFF1A1A2E),
                border: Border(
                  end: BorderSide(
                    color: const Color(0xFF2A2A45),
                    width: 0.5,
                  ),
                ),
              ),
              child: SafeArea(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Padding(
                      padding: const EdgeInsets.all(20),
                      child: Row(
                        children: [
                          Container(
                            width: 40,
                            height: 40,
                            decoration: BoxDecoration(
                              gradient: AppTheme.primaryGradient,
                              borderRadius: BorderRadius.circular(12),
                            ),
                            child: const Icon(Icons.auto_awesome, color: Colors.white, size: 20),
                          ),
                          const SizedBox(width: 12),
                          Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const Text(
                                'آدم بريزم',
                                style: TextStyle(
                                  color: Colors.white,
                                  fontSize: 16,
                                  fontWeight: FontWeight.w700,
                                ),
                              ),
                              Text(
                                settingsState.connectionSuccess ? 'متصل' : 'غير متصل',
                                style: TextStyle(
                                  color: settingsState.connectionSuccess
                                      ? const Color(0xFF00E676)
                                      : const Color(0xFF6B6B8D),
                                  fontSize: 11,
                                ),
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),
                    const Divider(color: Color(0xFF2A2A45), height: 1),
                    const SizedBox(height: 8),
                    _DesktopNavItem(
                      icon: Icons.chat,
                      label: 'المحادثة',
                      isSelected: _currentIndex == 0,
                      onTap: () => setState(() => _currentIndex = 0),
                    ),
                    _DesktopNavItem(
                      icon: Icons.history,
                      label: 'المحادثات',
                      isSelected: _currentIndex == 1,
                      onTap: () => setState(() => _currentIndex = 1),
                    ),
                    _DesktopNavItem(
                      icon: Icons.auto_stories,
                      label: 'المعرفة',
                      isSelected: _currentIndex == 2,
                      onTap: () => setState(() => _currentIndex = 2),
                    ),
                    _DesktopNavItem(
                      icon: Icons.psychology,
                      label: 'الذاكرة',
                      isSelected: _currentIndex == 3,
                      onTap: () => setState(() => _currentIndex = 3),
                    ),
                    _DesktopNavItem(
                      icon: Icons.build,
                      label: 'الأدوات والمهارات',
                      isSelected: _currentIndex == 4,
                      onTap: () => setState(() => _currentIndex = 4),
                    ),
                    const Spacer(),
                    const Divider(color: Color(0xFF2A2A45), height: 1),
                    _DesktopNavItem(
                      icon: Icons.settings,
                      label: 'الإعدادات',
                      isSelected: false,
                      onTap: () => _navigateToSettings(),
                    ),
                    const SizedBox(height: 8),
                  ],
                ),
              ),
            ),

            // Main content
            Expanded(
              child: IndexedStack(
                index: _currentIndex,
                children: _screens,
              ),
            ),
          ],
        ),
      ),
    );
  }

  void _navigateToSettings() {
    Navigator.of(context).push(
      PageRouteBuilder(
        pageBuilder: (context, animation, secondaryAnimation) =>
            const SettingsScreen(),
        transitionsBuilder: (context, animation, secondaryAnimation, child) {
          return SlideTransition(
            position: Tween<Offset>(
              begin: const Offset(1.0, 0.0),
              end: Offset.zero,
            ).animate(CurvedAnimation(
              parent: animation,
              curve: Curves.easeOutCubic,
            )),
            child: child,
          );
        },
      ),
    );
  }
}

// Bottom nav item for phone
class _NavItem extends StatelessWidget {
  final IconData icon;
  final String label;
  final bool isSelected;
  final VoidCallback onTap;

  const _NavItem({
    required this.icon,
    required this.label,
    required this.isSelected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      behavior: HitTestBehavior.opaque,
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 6),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            AnimatedContainer(
              duration: const Duration(milliseconds: 200),
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
              decoration: BoxDecoration(
                color: isSelected
                    ? const Color(0xFF6C63FF).withValues(alpha: 0.15)
                    : Colors.transparent,
                borderRadius: BorderRadius.circular(12),
              ),
              child: Icon(
                icon,
                color: isSelected ? const Color(0xFF6C63FF) : const Color(0xFF6B6B8D),
                size: 22,
              ),
            ),
            const SizedBox(height: 4),
            Text(
              label,
              style: TextStyle(
                color: isSelected ? const Color(0xFF6C63FF) : const Color(0xFF6B6B8D),
                fontSize: 10,
                fontWeight: isSelected ? FontWeight.w600 : FontWeight.w400,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// Side nav item for tablet
class _SideNavItem extends StatelessWidget {
  final IconData icon;
  final String label;
  final bool isSelected;
  final VoidCallback onTap;

  const _SideNavItem({
    required this.icon,
    required this.label,
    required this.isSelected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 12),
        child: Column(
          children: [
            AnimatedContainer(
              duration: const Duration(milliseconds: 200),
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: isSelected
                    ? const Color(0xFF6C63FF).withValues(alpha: 0.15)
                    : Colors.transparent,
                borderRadius: BorderRadius.circular(12),
              ),
              child: Icon(
                icon,
                color: isSelected ? const Color(0xFF6C63FF) : const Color(0xFF6B6B8D),
                size: 22,
              ),
            ),
            const SizedBox(height: 4),
            Text(
              label,
              style: TextStyle(
                color: isSelected ? const Color(0xFF6C63FF) : const Color(0xFF6B6B8D),
                fontSize: 9,
                fontWeight: isSelected ? FontWeight.w600 : FontWeight.w400,
              ),
              textAlign: TextAlign.center,
              maxLines: 1,
            ),
          ],
        ),
      ),
    );
  }
}

// Desktop nav item
class _DesktopNavItem extends StatelessWidget {
  final IconData icon;
  final String label;
  final bool isSelected;
  final VoidCallback onTap;

  const _DesktopNavItem({
    required this.icon,
    required this.label,
    required this.isSelected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Container(
          margin: const EdgeInsets.symmetric(horizontal: 12, vertical: 2),
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
          decoration: BoxDecoration(
            color: isSelected
                ? const Color(0xFF6C63FF).withValues(alpha: 0.12)
                : Colors.transparent,
            borderRadius: BorderRadius.circular(10),
          ),
          child: Row(
            children: [
              Icon(
                icon,
                color: isSelected ? const Color(0xFF6C63FF) : const Color(0xFF6B6B8D),
                size: 20,
              ),
              const SizedBox(width: 12),
              Text(
                label,
                style: TextStyle(
                  color: isSelected ? const Color(0xFF6C63FF) : const Color(0xFF9E9EB8),
                  fontSize: 14,
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
