class AppConstants {
  AppConstants._();

  // App Info
  static const String appName = 'Adam Prism';
  static const String appVersion = '1.0.0';
  static const String appTagline = 'مساعدك الذكي';

  // Default API
  static const String defaultBackendUrl = 'http://localhost:8000';
  static const String defaultApiVersion = '/api';

  // Storage Keys
  static const String onboardingCompleteKey = 'onboarding_complete';
  static const String backendUrlKey = 'backend_url';
  static const String apiKeyKey = 'api_key';
  static const String themeKey = 'theme_mode';
  static const String localeKey = 'locale';
  static const String selectedModelKey = 'selected_model';
  static const String voiceEnabledKey = 'voice_enabled';
  static const String notificationsEnabledKey = 'notifications_enabled';
  static const String sessionIdKey = 'current_session_id';

  // Timeouts
  static const Duration connectionTimeout = Duration(seconds: 10);
  static const Duration readTimeout = Duration(seconds: 30);
  static const Duration sseReconnectDelay = Duration(seconds: 2);

  // Chat
  static const int maxMessageLength = 4000;
  static const int messagesPerPage = 50;
  static const int sessionsPerPage = 20;
  static const int searchDebounceMs = 300;

  // Animation
  static const Duration animationDuration = Duration(milliseconds: 300);
  static const Duration shortAnimation = Duration(milliseconds: 150);

  // Layout breakpoints
  static const double phoneBreakpoint = 600;
  static const double tabletBreakpoint = 900;
  static const double desktopBreakpoint = 1200;

  // Voice
  static const int sampleRate = 44100;
  static const int bitRate = 128000;

  // Slash Commands
  static const Map<String, String> slashCommands = {
    '/new': 'Create a new chat session',
    '/clear': 'Clear the current conversation',
    '/memory': 'Browse stored memories',
    '/help': 'Show available commands',
  };
}
