import 'dart:io';
import 'package:flutter/material.dart';
import 'package:uuid/uuid.dart';
import '../constants/app_constants.dart';

class Helpers {
  Helpers._();

  static const _uuid = Uuid();

  static String generateId() => _uuid.v4();

  static String generateSessionId() => 'session_${_uuid.v4().substring(0, 8)}';

  static String formatBytes(int bytes) {
    if (bytes < 1024) return '$bytes B';
    if (bytes < 1048576) return '${(bytes / 1024).toStringAsFixed(1)} KB';
    if (bytes < 1073741824) return '${(bytes / 1048576).toStringAsFixed(1)} MB';
    return '${(bytes / 1073741824).toStringAsFixed(1)} GB';
  }

  static String formatDuration(Duration duration) {
    final hours = duration.inHours;
    final minutes = duration.inMinutes.remainder(60);
    final seconds = duration.inSeconds.remainder(60);

    if (hours > 0) {
      return '${hours}h ${minutes}m';
    }
    if (minutes > 0) {
      return '${minutes}m ${seconds}s';
    }
    return '${seconds}s';
  }

  static bool get isDesktop => Platform.isMacOS || Platform.isWindows || Platform.isLinux;

  static bool get isMobile => Platform.isAndroid || Platform.isIOS;

  static LayoutType getLayoutType(double width) {
    if (width < AppConstants.phoneBreakpoint) return LayoutType.phone;
    if (width < AppConstants.desktopBreakpoint) return LayoutType.tablet;
    return LayoutType.desktop;
  }

  static int getGridColumns(double width) {
    if (width < AppConstants.phoneBreakpoint) return 1;
    if (width < AppConstants.tabletBreakpoint) return 2;
    if (width < AppConstants.desktopBreakpoint) return 3;
    return 4;
  }

  static String extractCodeLanguage(String codeBlock) {
    final lines = codeBlock.split('\n');
    if (lines.isEmpty) return 'text';
    final firstLine = lines[0].trim();
    if (firstLine.startsWith('```')) {
      return firstLine.substring(3).trim().split(' ').first;
    }
    return 'text';
  }

  static Color getStatusColor(String status) {
    switch (status.toLowerCase()) {
      case 'online':
      case 'healthy':
      case 'active':
      case 'running':
        return const Color(0xFF00E676);
      case 'warning':
      case 'degraded':
        return const Color(0xFFFF9800);
      case 'offline':
      case 'error':
      case 'unhealthy':
      case 'failed':
        return const Color(0xFFFF5252);
      default:
        return const Color(0xFF6B6B8D);
    }
  }

  static IconData getStatusIcon(String status) {
    switch (status.toLowerCase()) {
      case 'online':
      case 'healthy':
      case 'active':
      case 'running':
        return Icons.check_circle;
      case 'warning':
      case 'degraded':
        return Icons.warning;
      case 'offline':
      case 'error':
      case 'unhealthy':
      case 'failed':
        return Icons.error;
      default:
        return Icons.help;
    }
  }

  static String maskApiKey(String key) {
    if (key.length <= 8) return '****';
    return '${key.substring(0, 4)}${'*' * (key.length - 8)}${key.substring(key.length - 4)}';
  }

  static String truncateWithEllipsis(String text, int maxLength) {
    if (text.length <= maxLength) return text;
    return '${text.substring(0, maxLength)}...';
  }
}

enum LayoutType { phone, tablet, desktop }
