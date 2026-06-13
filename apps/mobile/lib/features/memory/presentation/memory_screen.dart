import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/theme/app_theme.dart';
import '../../../models/memory.dart';
import '../providers/memory_provider.dart';

class MemoryScreen extends ConsumerStatefulWidget {
  const MemoryScreen({super.key});

  @override
  ConsumerState<MemoryScreen> createState() => _MemoryScreenState();
}

class _MemoryScreenState extends ConsumerState<MemoryScreen> {
  final _searchController = TextEditingController();
  final _contentController = TextEditingController();
  final _categoryController = TextEditingController();

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      ref.read(memoryProvider.notifier).loadStats();
    });
  }

  @override
  void dispose() {
    _searchController.dispose();
    _contentController.dispose();
    _categoryController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(memoryProvider);

    return Container(
      decoration: const BoxDecoration(color: Color(0xFF0F0F1A)),
      child: Column(
        children: [
          // Header with stats
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
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      const Text(
                        'الذاكرة',
                        style: TextStyle(
                          color: Colors.white,
                          fontSize: 24,
                          fontWeight: FontWeight.w800,
                        ),
                      ),
                      const Spacer(),
                      IconButton(
                        icon: Container(
                          padding: const EdgeInsets.all(8),
                          decoration: BoxDecoration(
                            color: const Color(0xFF6C63FF).withValues(alpha: 0.15),
                            borderRadius: BorderRadius.circular(10),
                          ),
                          child: const Icon(Icons.add, color: Color(0xFF6C63FF), size: 18),
                        ),
                        onPressed: () => _showStoreMemoryDialog(),
                      ),
                    ],
                  ),

                  // Stats cards
                  if (state.stats != null) ...[
                    const SizedBox(height: 12),
                    Row(
                      children: [
                        _StatCard(
                          label: 'إجمالي الذكريات',
                          value: '${state.stats!.totalMemories}',
                          icon: Icons.psychology,
                          color: const Color(0xFF6C63FF),
                        ),
                        const SizedBox(width: 10),
                        _StatCard(
                          label: 'الفئات',
                          value: '${state.stats!.totalCategories}',
                          icon: Icons.category,
                          color: const Color(0xFF00D9FF),
                        ),
                      ],
                    ),
                  ],

                  const SizedBox(height: 12),

                  // Search bar
                  Container(
                    decoration: BoxDecoration(
                      color: const Color(0xFF1E1E32),
                      borderRadius: BorderRadius.circular(14),
                      border: Border.all(color: const Color(0xFF2A2A45), width: 0.5),
                    ),
                    child: TextField(
                      controller: _searchController,
                      onSubmitted: (query) {
                        if (query.isNotEmpty) {
                          ref.read(memoryProvider.notifier).searchMemory(query);
                        }
                      },
                      style: const TextStyle(color: Colors.white, fontSize: 14),
                      decoration: InputDecoration(
                        hintText: 'البحث في الذاكرة...',
                        hintStyle: const TextStyle(color: Color(0xFF6B6B8D)),
                        prefixIcon: const Icon(Icons.search, color: Color(0xFF6B6B8D), size: 20),
                        suffixIcon: _searchController.text.isNotEmpty
                            ? IconButton(
                                icon: const Icon(Icons.clear, color: Color(0xFF6B6B8D)),
                                onPressed: () {
                                  _searchController.clear();
                                  ref.read(memoryProvider.notifier).clearSearch();
                                },
                              )
                            : null,
                        border: InputBorder.none,
                        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),

          // Content
          Expanded(
            child: state.isLoading
                ? const Center(child: CircularProgressIndicator(color: Color(0xFF6C63FF)))
                : state.memories.isNotEmpty
                    ? _buildMemoryList(state.memories)
                    : _buildEmptyState(),
          ),
        ],
      ),
    );
  }

  Widget _buildMemoryList(List<MemoryEntry> memories) {
    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: memories.length,
      itemBuilder: (context, index) {
        final memory = memories[index];
        return Container(
          margin: const EdgeInsets.only(bottom: 12),
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: const Color(0xFF1E1E32),
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: const Color(0xFF2A2A45), width: 0.5),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  if (memory.category != null)
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                      decoration: BoxDecoration(
                        color: const Color(0xFF00D9FF).withValues(alpha: 0.1),
                        borderRadius: BorderRadius.circular(6),
                      ),
                      child: Text(
                        memory.category!,
                        style: const TextStyle(
                          color: Color(0xFF00D9FF),
                          fontSize: 11,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ),
                  const Spacer(),
                  if (memory.relevanceScore != null)
                    Text(
                      '${(memory.relevanceScore! * 100).toStringAsFixed(0)}%',
                      style: TextStyle(
                        color: memory.relevanceScore! > 0.8
                            ? const Color(0xFF00E676)
                            : const Color(0xFFFF9800),
                        fontSize: 12,
                      ),
                    ),
                  const SizedBox(width: 8),
                  Text(
                    memory.createdAt.toString().substring(0, 10),
                    style: const TextStyle(color: Color(0xFF4A4A6A), fontSize: 11),
                  ),
                ],
              ),
              const SizedBox(height: 10),
              Text(
                memory.content,
                style: const TextStyle(
                  color: Color(0xFFE0E0EE),
                  fontSize: 14,
                  height: 1.6,
                ),
              ),
            ],
          ),
        );
      },
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 40),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              width: 80,
              height: 80,
              decoration: BoxDecoration(
                color: const Color(0xFF1E1E32),
                borderRadius: BorderRadius.circular(24),
              ),
              child: const Icon(Icons.psychology, color: Color(0xFF6B6B8D), size: 36),
            ),
            const SizedBox(height: 20),
            const Text(
              'لا توجد ذكريات',
              style: TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.w600),
            ),
            const SizedBox(height: 8),
            const Text(
              'ابحث في الذاكرة أو أضف ذكرى جديدة',
              style: TextStyle(color: Color(0xFF6B6B8D), fontSize: 14),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }

  void _showStoreMemoryDialog() {
    _contentController.clear();
    _categoryController.clear();

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: const Color(0xFF1E1E32),
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      builder: (context) => Padding(
        padding: EdgeInsets.only(
          left: 20,
          right: 20,
          top: 20,
          bottom: MediaQuery.of(context).viewInsets.bottom + 20,
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Center(
              child: Container(
                width: 40,
                height: 4,
                decoration: BoxDecoration(
                  color: const Color(0xFF2A2A45),
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
            ),
            const SizedBox(height: 20),
            const Text(
              'حفظ ذكرى جديدة',
              style: TextStyle(
                color: Colors.white,
                fontSize: 20,
                fontWeight: FontWeight.w700,
              ),
            ),
            const SizedBox(height: 20),
            TextField(
              controller: _contentController,
              maxLines: 4,
              style: const TextStyle(color: Colors.white),
              decoration: InputDecoration(
                hintText: 'محتوى الذاكرة',
                hintStyle: const TextStyle(color: Color(0xFF6B6B8D)),
              ),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _categoryController,
              style: const TextStyle(color: Colors.white),
              decoration: InputDecoration(
                hintText: 'الفئة (اختياري)',
                hintStyle: const TextStyle(color: Color(0xFF6B6B8D)),
              ),
            ),
            const SizedBox(height: 20),
            SizedBox(
              width: double.infinity,
              height: 50,
              child: ElevatedButton(
                onPressed: () {
                  if (_contentController.text.isNotEmpty) {
                    ref.read(memoryProvider.notifier).storeMemory(
                      content: _contentController.text,
                      category: _categoryController.text.isNotEmpty ? _categoryController.text : null,
                    );
                    Navigator.pop(context);
                  }
                },
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF6C63FF),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(14),
                  ),
                ),
                child: const Text(
                  'حفظ',
                  style: TextStyle(fontWeight: FontWeight.w700, fontSize: 16),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _StatCard extends StatelessWidget {
  final String label;
  final String value;
  final IconData icon;
  final Color color;

  const _StatCard({
    required this.label,
    required this.value,
    required this.icon,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: color.withValues(alpha: 0.08),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: color.withValues(alpha: 0.2), width: 0.5),
        ),
        child: Row(
          children: [
            Icon(icon, color: color, size: 20),
            const SizedBox(width: 10),
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  value,
                  style: TextStyle(
                    color: color,
                    fontSize: 18,
                    fontWeight: FontWeight.w700,
                  ),
                ),
                Text(
                  label,
                  style: TextStyle(
                    color: color.withValues(alpha: 0.7),
                    fontSize: 10,
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
