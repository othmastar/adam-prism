import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

extension BuildContextExtensions on BuildContext {
  ThemeData get theme => Theme.of(this);
  TextTheme get textTheme => Theme.of(this).textTheme;
  ColorScheme get colorScheme => Theme.of(this).colorScheme;
  MediaQueryData get mediaQuery => MediaQuery.of(this);
  Size get screenSize => MediaQuery.of(this).size;
  double get screenWidth => MediaQuery.of(this).size.width;
  double get screenHeight => MediaQuery.of(this).size.height;
  bool get isRTL => Directionality.of(this) == TextDirection.rtl;
  bool get isPhone => screenWidth < 600;
  bool get isTablet => screenWidth >= 600 && screenWidth < 1200;
  bool get isDesktop => screenWidth >= 1200;
  EdgeInsets get padding => MediaQuery.of(this).padding;
  EdgeInsets get viewInsets => MediaQuery.of(this).viewInsets;
}

extension StringExtensions on String {
  String get capitalized {
    if (isEmpty) return this;
    return '${this[0].toUpperCase()}${substring(1)}';
  }

  String get truncated {
    if (length <= 50) return this;
    return '${substring(0, 50)}...';
  }

  bool get isValidUrl {
    try {
      Uri.parse(this);
      return startsWith('http://') || startsWith('https://');
    } catch (_) {
      return false;
    }
  }

  String get removeWhitespace => replaceAll(RegExp(r'\s+'), ' ').trim();
}

extension DateTimeExtensions on DateTime {
  String get timeAgo {
    final now = DateTime.now();
    final diff = now.difference(this);

    if (diff.inMinutes < 1) return 'الآن';
    if (diff.inMinutes < 60) return 'منذ ${diff.inMinutes} دقيقة';
    if (diff.inHours < 24) return 'منذ ${diff.inHours} ساعة';
    if (diff.inDays < 2) return 'أمس';
    if (diff.inDays < 7) return 'منذ ${diff.inDays} أيام';
    if (diff.inDays < 30) return 'منذ ${(diff.inDays / 7).floor()} أسبوع';
    return DateFormat('yyyy/MM/dd').format(this);
  }

  String get formattedTime => DateFormat('HH:mm').format(this);

  String get formattedDate => DateFormat('yyyy/MM/dd').format(this);

  String get formattedDateTime => DateFormat('yyyy/MM/dd HH:mm').format(this);

  bool get isToday {
    final now = DateTime.now();
    return year == now.year && month == now.month && day == now.day;
  }

  bool get isYesterday {
    final yesterday = DateTime.now().subtract(const Duration(days: 1));
    return year == yesterday.year && month == yesterday.month && day == yesterday.day;
  }

  String get groupLabel {
    if (isToday) return 'اليوم';
    if (isYesterday) return 'أمس';
    if (DateTime.now().difference(this).inDays < 7) return 'هذا الأسبوع';
    if (DateTime.now().difference(this).inDays < 30) return 'هذا الشهر';
    return 'أقدم';
  }
}

extension ListExtensions<T> on List<T> {
  List<T> get distinct => [...{...this}];

  Map<S, List<T>> groupBy<S>(S Function(T) keySelector) {
    final map = <S, List<T>>{};
    for (final item in this) {
      (map[keySelector(item)] ??= []).add(item);
    }
    return map;
  }
}
