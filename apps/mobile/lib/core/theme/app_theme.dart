import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../constants/app_constants.dart';

class AppTheme {
  AppTheme._();

  static ThemeData get darkTheme => _buildDarkTheme();
  static ThemeData get lightTheme => _buildLightTheme();

  static ThemeData _buildDarkTheme() {
    final colorScheme = ColorScheme.fromSeed(
      seedColor: const Color(0xFF6C63FF),
      brightness: Brightness.dark,
      primary: const Color(0xFF6C63FF),
      secondary: const Color(0xFF00D9FF),
      surface: const Color(0xFF1A1A2E),
      error: const Color(0xFFFF5252),
      onPrimary: Colors.white,
      onSecondary: Colors.black,
      onSurface: Colors.white,
    );

    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.dark,
      colorScheme: colorScheme,
      scaffoldBackgroundColor: const Color(0xFF0F0F1A),
      canvasColor: const Color(0xFF1A1A2E),
      cardColor: const Color(0xFF1E1E32),
      dividerColor: const Color(0xFF2A2A45),
      dialogBackgroundColor: const Color(0xFF1E1E32),

      textTheme: GoogleFonts.notoSansArabicTextTheme(
        ThemeData(brightness: Brightness.dark).textTheme,
      ).apply(
        bodyColor: Colors.white,
        displayColor: Colors.white,
      ),

      appBarTheme: AppBarTheme(
        elevation: 0,
        centerTitle: false,
        backgroundColor: Colors.transparent,
        surfaceTintColor: Colors.transparent,
        titleTextStyle: GoogleFonts.notoSansArabic(
          color: Colors.white,
          fontSize: 22,
          fontWeight: FontWeight.w700,
        ),
        iconTheme: const IconThemeData(color: Colors.white),
      ),

      cardTheme: CardTheme(
        elevation: 0,
        color: const Color(0xFF1E1E32),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
          side: BorderSide(color: const Color(0xFF2A2A45), width: 0.5),
        ),
        margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
      ),

      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          elevation: 0,
          backgroundColor: const Color(0xFF6C63FF),
          foregroundColor: Colors.white,
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
          ),
          textStyle: GoogleFonts.notoSansArabic(
            fontSize: 16,
            fontWeight: FontWeight.w600,
          ),
        ),
      ),

      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          foregroundColor: const Color(0xFF6C63FF),
          side: const BorderSide(color: Color(0xFF6C63FF)),
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
          ),
          textStyle: GoogleFonts.notoSansArabic(
            fontSize: 16,
            fontWeight: FontWeight.w600,
          ),
        ),
      ),

      textButtonTheme: TextButtonThemeData(
        style: TextButton.styleFrom(
          foregroundColor: const Color(0xFF6C63FF),
          textStyle: GoogleFonts.notoSansArabic(
            fontSize: 14,
            fontWeight: FontWeight.w600,
          ),
        ),
      ),

      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: const Color(0xFF1E1E32),
        hintStyle: GoogleFonts.notoSansArabic(
          color: const Color(0xFF6B6B8D),
        ),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide.none,
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide.none,
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: Color(0xFF6C63FF), width: 2),
        ),
        errorBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: Color(0xFFFF5252)),
        ),
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      ),

      bottomNavigationBarTheme: const BottomNavigationBarThemeData(
        backgroundColor: Color(0xFF1A1A2E),
        selectedItemColor: Color(0xFF6C63FF),
        unselectedItemColor: Color(0xFF6B6B8D),
        type: BottomNavigationBarType.fixed,
        elevation: 8,
      ),

      navigationRailTheme: NavigationRailThemeData(
        backgroundColor: const Color(0xFF1A1A2E),
        indicatorColor: const Color(0xFF6C63FF).withValues(alpha: 0.2),
        selectedIconTheme: const IconThemeData(color: Color(0xFF6C63FF)),
        unselectedIconTheme: const IconThemeData(color: Color(0xFF6B6B8D)),
        selectedLabelTextStyle: GoogleFonts.notoSansArabic(
          color: const Color(0xFF6C63FF),
          fontWeight: FontWeight.w600,
          fontSize: 12,
        ),
        unselectedLabelTextStyle: GoogleFonts.notoSansArabic(
          color: const Color(0xFF6B6B8D),
          fontSize: 12,
        ),
      ),

      floatingActionButtonTheme: FloatingActionButtonThemeData(
        backgroundColor: const Color(0xFF6C63FF),
        foregroundColor: Colors.white,
        elevation: 4,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
        ),
      ),

      dialogTheme: DialogTheme(
        backgroundColor: const Color(0xFF1E1E32),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(20),
        ),
        titleTextStyle: GoogleFonts.notoSansArabic(
          color: Colors.white,
          fontSize: 20,
          fontWeight: FontWeight.w700,
        ),
      ),

      snackBarTheme: SnackBarThemeData(
        backgroundColor: const Color(0xFF1E1E32),
        contentTextStyle: GoogleFonts.notoSansArabic(color: Colors.white),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
        ),
        behavior: SnackBarBehavior.floating,
      ),

      chipTheme: ChipThemeData(
        backgroundColor: const Color(0xFF2A2A45),
        selectedColor: const Color(0xFF6C63FF),
        labelStyle: GoogleFonts.notoSansArabic(
          color: Colors.white,
          fontSize: 13,
        ),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(8),
        ),
      ),

      progressIndicatorTheme: const ProgressIndicatorThemeData(
        color: Color(0xFF6C63FF),
        linearTrackColor: Color(0xFF2A2A45),
      ),

      tabBarTheme: TabBarTheme(
        labelColor: const Color(0xFF6C63FF),
        unselectedLabelColor: const Color(0xFF6B6B8D),
        indicatorColor: const Color(0xFF6C63FF),
        labelStyle: GoogleFonts.notoSansArabic(
          fontWeight: FontWeight.w600,
          fontSize: 14,
        ),
        unselectedLabelStyle: GoogleFonts.notoSansArabic(
          fontWeight: FontWeight.w400,
          fontSize: 14,
        ),
      ),

      listTileTheme: ListTileThemeData(
        textColor: Colors.white,
        iconColor: const Color(0xFF6B6B8D),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
        ),
      ),

      switchTheme: SwitchThemeData(
        thumbColor: WidgetStateProperty.resolveWith((states) {
          if (states.contains(WidgetState.selected)) {
            return const Color(0xFF6C63FF);
          }
          return const Color(0xFF6B6B8D);
        }),
        trackColor: WidgetStateProperty.resolveWith((states) {
          if (states.contains(WidgetState.selected)) {
            return const Color(0xFF6C63FF).withValues(alpha: 0.5);
          }
          return const Color(0xFF2A2A45);
        }),
      ),

      sliderTheme: SliderThemeData(
        activeTrackColor: const Color(0xFF6C63FF),
        inactiveTrackColor: const Color(0xFF2A2A45),
        thumbColor: const Color(0xFF6C63FF),
      ),
    );
  }

  static ThemeData _buildLightTheme() {
    final colorScheme = ColorScheme.fromSeed(
      seedColor: const Color(0xFF6C63FF),
      brightness: Brightness.light,
      primary: const Color(0xFF6C63FF),
      secondary: const Color(0xFF00B8D9),
      surface: Colors.white,
      error: const Color(0xFFD32F2F),
    );

    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.light,
      colorScheme: colorScheme,
      scaffoldBackgroundColor: const Color(0xFFF5F5FA),
      canvasColor: Colors.white,
      cardColor: Colors.white,
      dividerColor: const Color(0xFFE0E0EE),
      dialogBackgroundColor: Colors.white,

      textTheme: GoogleFonts.notoSansArabicTextTheme(
        ThemeData(brightness: Brightness.light).textTheme,
      ),

      appBarTheme: AppBarTheme(
        elevation: 0,
        centerTitle: false,
        backgroundColor: Colors.transparent,
        surfaceTintColor: Colors.transparent,
        titleTextStyle: GoogleFonts.notoSansArabic(
          color: const Color(0xFF1A1A2E),
          fontSize: 22,
          fontWeight: FontWeight.w700,
        ),
        iconTheme: const IconThemeData(color: Color(0xFF1A1A2E)),
      ),

      cardTheme: CardTheme(
        elevation: 1,
        color: Colors.white,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
          side: BorderSide(color: const Color(0xFFE0E0EE), width: 0.5),
        ),
        margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
      ),

      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          elevation: 0,
          backgroundColor: const Color(0xFF6C63FF),
          foregroundColor: Colors.white,
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
          ),
        ),
      ),

      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: const Color(0xFFF0F0FA),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide.none,
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide.none,
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: Color(0xFF6C63FF), width: 2),
        ),
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      ),

      bottomNavigationBarTheme: const BottomNavigationBarThemeData(
        backgroundColor: Colors.white,
        selectedItemColor: Color(0xFF6C63FF),
        unselectedItemColor: Color(0xFF9E9EB8),
        type: BottomNavigationBarType.fixed,
        elevation: 8,
      ),

      floatingActionButtonTheme: FloatingActionButtonThemeData(
        backgroundColor: const Color(0xFF6C63FF),
        foregroundColor: Colors.white,
        elevation: 4,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
        ),
      ),
    );
  }

  // Gradient for app bars and headers
  static LinearGradient get primaryGradient => const LinearGradient(
    colors: [Color(0xFF6C63FF), Color(0xFF00D9FF)],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );

  static LinearGradient get cardGradient => const LinearGradient(
    colors: [Color(0xFF1E1E32), Color(0xFF2A2A45)],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );

  // Custom colors
  static const Color userBubbleColor = Color(0xFF6C63FF);
  static const Color assistantBubbleColor = Color(0xFF1E1E32);
  static const Color systemBubbleColor = Color(0xFF2A2A45);
  static const Color onlineGreen = Color(0xFF00E676);
  static const Color warningOrange = Color(0xFFFF9800);
}
