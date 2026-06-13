import 'package:flutter/material.dart';

class SessionSearch extends StatefulWidget {
  final Function(String) onSearch;
  final VoidCallback onClear;

  const SessionSearch({
    super.key,
    required this.onSearch,
    required this.onClear,
  });

  @override
  State<SessionSearch> createState() => _SessionSearchState();
}

class _SessionSearchState extends State<SessionSearch> {
  final _controller = TextEditingController();
  bool _isSearching = false;

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: const Color(0xFF1E1E32),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(
          color: const Color(0xFF2A2A45),
          width: 0.5,
        ),
      ),
      child: TextField(
        controller: _controller,
        onChanged: (value) {
          if (value.isEmpty) {
            widget.onClear();
            setState(() => _isSearching = false);
          } else {
            widget.onSearch(value);
            setState(() => _isSearching = true);
          }
        },
        style: const TextStyle(color: Colors.white, fontSize: 14),
        decoration: InputDecoration(
          hintText: 'البحث في المحادثات...',
          hintStyle: const TextStyle(color: Color(0xFF6B6B8D), fontSize: 14),
          prefixIcon: const Icon(Icons.search, color: Color(0xFF6B6B8D), size: 20),
          suffixIcon: _isSearching
              ? IconButton(
                  icon: const Icon(Icons.clear, color: Color(0xFF6B6B8D), size: 18),
                  onPressed: () {
                    _controller.clear();
                    widget.onClear();
                    setState(() => _isSearching = false);
                  },
                )
              : null,
          border: InputBorder.none,
          contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        ),
      ),
    );
  }
}
