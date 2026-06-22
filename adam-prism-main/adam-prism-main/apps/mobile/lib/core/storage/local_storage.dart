import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:hive_flutter/hive_flutter.dart';
import '../constants/app_constants.dart';

class LocalStorage {
  LocalStorage._();

  static final LocalStorage instance = LocalStorage._();

  late final Box _settingsBox;
  late final Box _cacheBox;
  late final FlutterSecureStorage _secureStorage;

  Future<void> init() async {
    await Hive.initFlutter('adam_prism');
    _settingsBox = await Hive.openBox('settings');
    _cacheBox = await Hive.openBox('cache');
    _secureStorage = const FlutterSecureStorage(
      aOptions: AndroidOptions(encryptedSharedPreferences: true),
      iOptions: IOSOptions(accessibility: KeychainAccessibility.first_unlock),
    );
  }

  // Settings
  Future<void> setBool(String key, bool value) async {
    await _settingsBox.put(key, value);
  }

  bool getBool(String key, {bool defaultValue = false}) {
    return _settingsBox.get(key, defaultValue: defaultValue) as bool;
  }

  Future<void> setString(String key, String value) async {
    await _settingsBox.put(key, value);
  }

  String getString(String key, {String defaultValue = ''}) {
    return _settingsBox.get(key, defaultValue: defaultValue) as String;
  }

  Future<void> setInt(String key, int value) async {
    await _settingsBox.put(key, value);
  }

  int getInt(String key, {int defaultValue = 0}) {
    return _settingsBox.get(key, defaultValue: defaultValue) as int;
  }

  Future<void> remove(String key) async {
    await _settingsBox.delete(key);
  }

  // Secure storage for API keys
  Future<void> setSecure(String key, String value) async {
    await _secureStorage.write(key: key, value: value);
  }

  Future<String?> getSecure(String key) async {
    return await _secureStorage.read(key: key);
  }

  Future<void> deleteSecure(String key) async {
    await _secureStorage.delete(key: key);
  }

  // Cache
  Future<void> cacheData(String key, dynamic data, {Duration? ttl}) async {
    await _cacheBox.put(key, {
      'data': data,
      'timestamp': DateTime.now().millisecondsSinceEpoch,
      'ttl': ttl?.inMilliseconds,
    });
  }

  dynamic getCached(String key) {
    final entry = _cacheBox.get(key) as Map?;
    if (entry == null) return null;
    final timestamp = entry['timestamp'] as int;
    final ttl = entry['ttl'] as int?;
    if (ttl != null) {
      final age = DateTime.now().millisecondsSinceEpoch - timestamp;
      if (age > ttl) {
        _cacheBox.delete(key);
        return null;
      }
    }
    return entry['data'];
  }

  Future<void> clearCache() async {
    await _cacheBox.clear();
  }

  // Convenience methods for app settings
  bool get isOnboardingComplete =>
      getBool(AppConstants.onboardingCompleteKey);

  Future<void> setOnboardingComplete(bool value) =>
      setBool(AppConstants.onboardingCompleteKey, value);

  String get backendUrl =>
      getString(AppConstants.backendUrlKey, defaultValue: AppConstants.defaultBackendUrl);

  Future<void> setBackendUrl(String url) =>
      setString(AppConstants.backendUrlKey, url);

  Future<String?> get apiKey =>
      getSecure(AppConstants.apiKeyKey);

  Future<void> setApiKey(String key) =>
      setSecure(AppConstants.apiKeyKey, key);

  Future<void> deleteApiKey() =>
      deleteSecure(AppConstants.apiKeyKey);

  String get themeMode =>
      getString(AppConstants.themeKey, defaultValue: 'dark');

  Future<void> setThemeMode(String mode) =>
      setString(AppConstants.themeKey, mode);

  String get locale =>
      getString(AppConstants.localeKey, defaultValue: 'ar');

  Future<void> setLocale(String locale) =>
      setString(AppConstants.localeKey, locale);

  String get selectedModel =>
      getString(AppConstants.selectedModelKey, defaultValue: '');

  Future<void> setSelectedModel(String model) =>
      setString(AppConstants.selectedModelKey, model);
}
