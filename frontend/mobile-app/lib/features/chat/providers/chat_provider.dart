import 'dart:async';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/api/api_client.dart';
import '../../../core/api/sse_client.dart';
import '../../../core/storage/local_storage.dart';
import '../../../core/utils/helpers.dart';
import '../../../models/chat_message.dart';

class ChatState {
  final String? currentSessionId;
  final List<ChatMessage> messages;
  final bool isLoading;
  final bool isStreaming;
  final String streamingContent;
  final String? error;
  final List<ToolCall> activeToolCalls;

  const ChatState({
    this.currentSessionId,
    this.messages = const [],
    this.isLoading = false,
    this.isStreaming = false,
    this.streamingContent = '',
    this.error,
    this.activeToolCalls = const [],
  });

  ChatState copyWith({
    String? currentSessionId,
    List<ChatMessage>? messages,
    bool? isLoading,
    bool? isStreaming,
    String? streamingContent,
    String? error,
    List<ToolCall>? activeToolCalls,
  }) {
    return ChatState(
      currentSessionId: currentSessionId ?? this.currentSessionId,
      messages: messages ?? this.messages,
      isLoading: isLoading ?? this.isLoading,
      isStreaming: isStreaming ?? this.isStreaming,
      streamingContent: streamingContent ?? this.streamingContent,
      error: error,
      activeToolCalls: activeToolCalls ?? this.activeToolCalls,
    );
  }
}

class ChatNotifier extends StateNotifier<ChatState> {
  StreamSubscription? _streamSubscription;

  ChatNotifier() : super(const ChatState());

  void setSession(String? sessionId) {
    state = state.copyWith(
      currentSessionId: sessionId,
      messages: [],
      streamingContent: '',
      isStreaming: false,
      error: null,
    );
    if (sessionId != null) {
      _loadMessages(sessionId);
    }
  }

  Future<void> _loadMessages(String sessionId) async {
    state = state.copyWith(isLoading: true);
    try {
      final messagesJson = await ApiClient.instance.getSessionMessages(sessionId);
      final messages = messagesJson.map((m) {
        final role = m['role'] as String? ?? 'assistant';
        return ChatMessage(
          id: m['id'] as String? ?? Helpers.generateId(),
          sessionId: sessionId,
          role: _parseRole(role),
          content: m['content'] as String? ?? '',
          status: MessageStatus.complete,
          timestamp: m['timestamp'] != null
              ? DateTime.parse(m['timestamp'] as String)
              : DateTime.now(),
          model: m['model'] as String?,
          metadata: m['metadata'] as Map<String, dynamic>?,
        );
      }).toList();
      state = state.copyWith(messages: messages, isLoading: false);
    } catch (e) {
      state = state.copyWith(isLoading: false, error: e.toString());
    }
  }

  Future<void> sendMessage(String message) async {
    if (message.trim().isEmpty) return;

    // Handle slash commands
    if (message.startsWith('/')) {
      _handleSlashCommand(message);
      return;
    }

    final userMessage = ChatMessage(
      id: Helpers.generateId(),
      sessionId: state.currentSessionId ?? '',
      role: MessageRole.user,
      content: message,
      status: MessageStatus.sent,
      timestamp: DateTime.now(),
    );

    state = state.copyWith(
      messages: [...state.messages, userMessage],
      isStreaming: true,
      streamingContent: '',
      error: null,
    );

    try {
      final stream = ApiClient.instance.streamChat(
        message: message,
        sessionId: state.currentSessionId,
      );

      final chatStream = SseClient.parseChatStream(stream);
      final buffer = StringBuffer();

      _streamSubscription?.cancel();
      _streamSubscription = chatStream.listen(
        (event) {
          switch (event.type) {
            case 'token':
              buffer.write(event.token);
              state = state.copyWith(
                streamingContent: buffer.toString(),
              );
              break;
            case 'complete':
              final assistantMessage = ChatMessage(
                id: Helpers.generateId(),
                sessionId: state.currentSessionId ?? '',
                role: MessageRole.assistant,
                content: buffer.toString(),
                status: MessageStatus.complete,
                timestamp: DateTime.now(),
                metadata: event.message,
              );

              // Update session ID if new
              final newSessionId = event.message?['session_id'] as String?;
              state = state.copyWith(
                messages: [...state.messages, assistantMessage],
                isStreaming: false,
                streamingContent: '',
                currentSessionId: newSessionId ?? state.currentSessionId,
              );

              // Save session ID
              if (newSessionId != null) {
                LocalStorage.instance.setString(
                  'current_session_id',
                  newSessionId,
                );
              }
              break;
            case 'error':
              state = state.copyWith(
                isStreaming: false,
                streamingContent: '',
                error: event.error,
              );
              break;
            case 'tool_call':
              final toolCall = ToolCall(
                id: Helpers.generateId(),
                name: event.toolName ?? '',
                arguments: event.toolArgs ?? {},
                status: ToolCallStatus.running,
              );
              state = state.copyWith(
                activeToolCalls: [...state.activeToolCalls, toolCall],
              );
              break;
            case 'tool_result':
              final updatedCalls = state.activeToolCalls.map((tc) {
                if (tc.name == event.toolName) {
                  return tc.copyWith(
                    result: event.toolResult,
                    status: ToolCallStatus.completed,
                  );
                }
                return tc;
              }).toList();
              state = state.copyWith(activeToolCalls: updatedCalls);
              break;
          }
        },
        onError: (error) {
          state = state.copyWith(
            isStreaming: false,
            streamingContent: '',
            error: error.toString(),
          );
        },
        onDone: () {
          // If stream ended without complete event, finalize
          if (state.isStreaming) {
            final assistantMessage = ChatMessage(
              id: Helpers.generateId(),
              sessionId: state.currentSessionId ?? '',
              role: MessageRole.assistant,
              content: state.streamingContent,
              status: MessageStatus.complete,
              timestamp: DateTime.now(),
            );
            state = state.copyWith(
              messages: [...state.messages, assistantMessage],
              isStreaming: false,
              streamingContent: '',
            );
          }
        },
      );
    } catch (e) {
      state = state.copyWith(
        isStreaming: false,
        streamingContent: '',
        error: e.toString(),
      );
    }
  }

  void _handleSlashCommand(String command) {
    switch (command.trim()) {
      case '/new':
        newChat();
        break;
      case '/clear':
        clearChat();
        break;
      case '/memory':
        // Navigation handled in UI
        break;
      case '/help':
        // Show help dialog - handled in UI
        break;
      default:
        state = state.copyWith(error: 'أمر غير معروف: $command');
    }
  }

  void newChat() {
    _streamSubscription?.cancel();
    state = state.copyWith(
      currentSessionId: null,
      messages: [],
      streamingContent: '',
      isStreaming: false,
      error: null,
      activeToolCalls: [],
    );
  }

  void clearChat() {
    _streamSubscription?.cancel();
    state = state.copyWith(
      messages: [],
      streamingContent: '',
      isStreaming: false,
      error: null,
      activeToolCalls: [],
    );
  }

  void retryLastMessage() {
    if (state.messages.isEmpty) return;
    final lastUserMessage = state.messages.lastWhere(
      (m) => m.role == MessageRole.user,
      orElse: () => state.messages.last,
    );
    // Remove last assistant message if exists
    final messages = state.messages.where((m) {
      if (m.role == MessageRole.assistant && m == state.messages.last) return false;
      return true;
    }).toList();
    state = state.copyWith(messages: messages, error: null);
    sendMessage(lastUserMessage.content);
  }

  void deleteMessage(String messageId) {
    state = state.copyWith(
      messages: state.messages.where((m) => m.id != messageId).toList(),
    );
  }

  @override
  void dispose() {
    _streamSubscription?.cancel();
    super.dispose();
  }

  MessageRole _parseRole(String role) {
    switch (role.toLowerCase()) {
      case 'user':
        return MessageRole.user;
      case 'assistant':
        return MessageRole.assistant;
      case 'system':
        return MessageRole.system;
      case 'tool':
        return MessageRole.tool;
      default:
        return MessageRole.assistant;
    }
  }
}

final chatProvider = StateNotifierProvider<ChatNotifier, ChatState>(
  (ref) => ChatNotifier(),
);
