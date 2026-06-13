import 'package:flutter/material.dart';
import '../../../core/theme/app_theme.dart';
import '../../../core/constants/app_constants.dart';
import 'voice_button.dart';

class ChatInput extends StatefulWidget {
  final Function(String) onSend;
  final bool isStreaming;
  final VoidCallback? onStop;

  const ChatInput({
    super.key,
    required this.onSend,
    this.isStreaming = false,
    this.onStop,
  });

  @override
  State<ChatInput> createState() => _ChatInputState();
}

class _ChatInputState extends State<ChatInput> {
  final _controller = TextEditingController();
  final _focusNode = FocusNode();
  bool _showSlashMenu = false;
  String _slashFilter = '';

  @override
  void dispose() {
    _controller.dispose();
    _focusNode.dispose();
    super.dispose();
  }

  void _handleSend() {
    final text = _controller.text.trim();
    if (text.isEmpty) return;
    widget.onSend(text);
    _controller.clear();
    setState(() => _showSlashMenu = false);
  }

  void _onTextChanged(String value) {
    if (value.startsWith('/') && !value.contains(' ')) {
      setState(() {
        _showSlashMenu = true;
        _slashFilter = value.toLowerCase();
      });
    } else {
      setState(() => _showSlashMenu = false);
    }
  }

  List<MapEntry<String, String>> get _filteredCommands {
    return AppConstants.slashCommands.entries
        .where((e) => e.key.toLowerCase().contains(_slashFilter))
        .toList();
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: const Color(0xFF1A1A2E),
        border: Border(
          top: BorderSide(
            color: const Color(0xFF2A2A45),
            width: 0.5,
          ),
        ),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          // Slash commands menu
          if (_showSlashMenu) _buildSlashMenu(),

          // Input row
          SafeArea(
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  // Voice button
                  VoiceButton(
                    onResult: (text) {
                      _controller.text = text;
                      _focusNode.requestFocus();
                    },
                  ),

                  const SizedBox(width: 8),

                  // Text input
                  Expanded(
                    child: Container(
                      constraints: const BoxConstraints(maxHeight: 120),
                      decoration: BoxDecoration(
                        color: const Color(0xFF1E1E32),
                        borderRadius: BorderRadius.circular(24),
                        border: Border.all(
                          color: const Color(0xFF2A2A45),
                          width: 0.5,
                        ),
                      ),
                      child: TextField(
                        controller: _controller,
                        focusNode: _focusNode,
                        onChanged: _onTextChanged,
                        maxLines: null,
                        textInputAction: TextInputAction.newline,
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 15,
                        ),
                        decoration: InputDecoration(
                          hintText: 'اكتب رسالتك هنا...',
                          hintStyle: const TextStyle(
                            color: Color(0xFF6B6B8D),
                            fontSize: 15,
                          ),
                          border: InputBorder.none,
                          contentPadding: const EdgeInsets.symmetric(
                            horizontal: 20,
                            vertical: 12,
                          ),
                          suffixIcon: _controller.text.isNotEmpty
                              ? IconButton(
                                  icon: const Icon(
                                    Icons.clear,
                                    color: Color(0xFF6B6B8D),
                                    size: 20,
                                  ),
                                  onPressed: () {
                                    _controller.clear();
                                    setState(() => _showSlashMenu = false);
                                  },
                                )
                              : null,
                        ),
                      ),
                    ),
                  ),

                  const SizedBox(width: 8),

                  // Send / Stop button
                  AnimatedSwitcher(
                    duration: const Duration(milliseconds: 200),
                    child: widget.isStreaming
                        ? _StopButton(onStop: widget.onStop ?? () {})
                        : _SendButton(
                            enabled: _controller.text.trim().isNotEmpty,
                            onTap: _handleSend,
                          ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSlashMenu() {
    final commands = _filteredCommands;
    if (commands.isEmpty) return const SizedBox.shrink();

    return Container(
      constraints: const BoxConstraints(maxHeight: 200),
      decoration: const BoxDecoration(
        color: Color(0xFF1E1E32),
        border: Border(
          bottom: BorderSide(color: Color(0xFF2A2A45), width: 0.5),
        ),
      ),
      child: ListView.builder(
        shrinkWrap: true,
        padding: const EdgeInsets.symmetric(vertical: 8),
        itemCount: commands.length,
        itemBuilder: (context, index) {
          final cmd = commands[index];
          return ListTile(
            dense: true,
            leading: Container(
              width: 32,
              height: 32,
              decoration: BoxDecoration(
                color: const Color(0xFF6C63FF).withValues(alpha: 0.1),
                borderRadius: BorderRadius.circular(8),
              ),
              child: const Icon(Icons.terminal, color: Color(0xFF6C63FF), size: 16),
            ),
            title: Text(
              cmd.key,
              style: const TextStyle(
                color: Color(0xFF00D9FF),
                fontSize: 14,
                fontWeight: FontWeight.w600,
                fontFamily: 'monospace',
              ),
            ),
            subtitle: Text(
              cmd.value,
              style: const TextStyle(
                color: Color(0xFF6B6B8D),
                fontSize: 12,
              ),
            ),
            onTap: () {
              _controller.text = '${cmd.key} ';
              _controller.selection = TextSelection.fromPosition(
                TextPosition(offset: _controller.text.length),
              );
              setState(() => _showSlashMenu = false);
              _focusNode.requestFocus();
            },
          );
        },
      ),
    );
  }
}

class _SendButton extends StatelessWidget {
  final bool enabled;
  final VoidCallback onTap;

  const _SendButton({required this.enabled, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 44,
      height: 44,
      decoration: BoxDecoration(
        gradient: enabled
            ? AppTheme.primaryGradient
            : LinearGradient(
                colors: [const Color(0xFF2A2A45), const Color(0xFF2A2A45)],
              ),
        borderRadius: BorderRadius.circular(22),
      ),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: enabled ? onTap : null,
          borderRadius: BorderRadius.circular(22),
          child: Icon(
            Icons.send,
            color: enabled ? Colors.white : const Color(0xFF6B6B8D),
            size: 20,
          ),
        ),
      ),
    );
  }
}

class _StopButton extends StatelessWidget {
  final VoidCallback onStop;

  const _StopButton({required this.onStop});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 44,
      height: 44,
      decoration: BoxDecoration(
        color: const Color(0xFFFF5252),
        borderRadius: BorderRadius.circular(22),
      ),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: onStop,
          borderRadius: BorderRadius.circular(22),
          child: const Icon(
            Icons.stop,
            color: Colors.white,
            size: 20,
          ),
        ),
      ),
    );
  }
}
