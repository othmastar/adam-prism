import 'package:flutter/material.dart';
import '../../../core/theme/app_theme.dart';

class VoiceButton extends StatefulWidget {
  final Function(String) onResult;

  const VoiceButton({super.key, required this.onResult});

  @override
  State<VoiceButton> createState() => _VoiceButtonState();
}

class _VoiceButtonState extends State<VoiceButton>
    with SingleTickerProviderStateMixin {
  bool _isRecording = false;
  late AnimationController _pulseController;
  late Animation<double> _pulseAnimation;

  @override
  void initState() {
    super.initState();
    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1200),
    )..repeat(reverse: true);
    _pulseAnimation = Tween<double>(begin: 1.0, end: 1.2).animate(
      CurvedAnimation(parent: _pulseController, curve: Curves.easeInOut),
    );
  }

  @override
  void dispose() {
    _pulseController.dispose();
    super.dispose();
  }

  Future<void> _toggleRecording() async {
    if (_isRecording) {
      // Stop recording and simulate transcription
      setState(() => _isRecording = false);
      _pulseController.stop();

      // Simulate voice transcription result
      // In production, this would use actual speech-to-text
      widget.onResult('نتيجة التعرف على الصوت');
    } else {
      // Start recording
      setState(() => _isRecording = true);
      _pulseController.repeat(reverse: true);

      // Auto-stop after a few seconds for demo
      // In production, this would use the record package
      Future.delayed(const Duration(seconds: 5), () {
        if (_isRecording && mounted) {
          _toggleRecording();
        }
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _pulseAnimation,
      builder: (context, child) {
        return Transform.scale(
          scale: _isRecording ? _pulseAnimation.value : 1.0,
          child: Container(
            width: 44,
            height: 44,
            decoration: BoxDecoration(
              color: _isRecording
                  ? const Color(0xFFFF5252).withValues(alpha: 0.2)
                  : const Color(0xFF1E1E32),
              borderRadius: BorderRadius.circular(22),
              border: Border.all(
                color: _isRecording
                    ? const Color(0xFFFF5252)
                    : const Color(0xFF2A2A45),
                width: _isRecording ? 2 : 0.5,
              ),
            ),
            child: Material(
              color: Colors.transparent,
              child: InkWell(
                onTap: _toggleRecording,
                borderRadius: BorderRadius.circular(22),
                child: Icon(
                  _isRecording ? Icons.stop : Icons.mic,
                  color: _isRecording
                      ? const Color(0xFFFF5252)
                      : const Color(0xFF6B6B8D),
                  size: 20,
                ),
              ),
            ),
          ),
        );
      },
    );
  }
}

class AnimatedBuilder extends AnimatedWidget {
  final Widget Function(BuildContext context, Widget? child) builder;
  final Widget? child;

  const AnimatedBuilder({
    super.key,
    required super.listenable,
    required this.builder,
    this.child,
  });

  @override
  Widget build(BuildContext context) {
    return builder(context, child);
  }
}
