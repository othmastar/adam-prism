/**
 * [PHASE3] Adam Prism Mobile — Chat screen
 */
import { useState, useRef } from "react"
import { View, Text, TextInput, Pressable, FlatList, ActivityIndicator, KeyboardAvoidingView, Platform, StyleSheet } from "react-native"
import { SafeAreaView } from "react-native-safe-area-context"
import { useChatStore, Message } from "../lib/chat"
import api from "../lib/api"

export function ChatScreen() {
  const [input, setInput] = useState("")
  const flatListRef = useRef<FlatList>(null)
  const { messages, isStreaming, addMessage, updateLastMessage, setStreaming, setError, error } = useChatStore()

  const send = async () => {
    const text = input.trim()
    if (!text || isStreaming) return
    setInput("")
    setError(null)

    // Add user message
    const userMsg: Message = {
      id: `${Date.now()}-u`,
      role: "user",
      content: text,
      timestamp: Date.now(),
    }
    addMessage(userMsg)

    // Add placeholder for assistant response
    const assistantId = `${Date.now()}-a`
    addMessage({
      id: assistantId,
      role: "assistant",
      content: "",
      timestamp: Date.now(),
    })

    setStreaming(true)
    try {
      const start = Date.now()
      const response = await api.chat(text)
      updateLastMessage(response.response)
      const final = useChatStore.getState().messages
      if (final.length > 0) {
        final[final.length - 1].duration_ms = Date.now() - start
      }
    } catch (e: any) {
      setError(e?.message || "Failed to send")
      updateLastMessage("❌ Failed to get response")
    } finally {
      setStreaming(false)
    }
  }

  return (
    <SafeAreaView style={styles.container} edges={["top"]}>
      <KeyboardAvoidingView
        style={styles.flex}
        behavior={Platform.OS === "ios" ? "padding" : undefined}
        keyboardVerticalOffset={90}
      >
        <FlatList
          ref={flatListRef}
          data={messages}
          keyExtractor={(item) => item.id}
          contentContainerStyle={styles.list}
          renderItem={({ item }) => (
            <View style={[styles.bubble, item.role === "user" ? styles.userBubble : styles.aiBubble]}>
              <Text style={[styles.role, item.role === "user" ? styles.userRole : styles.aiRole]}>
                {item.role === "user" ? "👤 You" : "🤖 آدم"}
              </Text>
              <Text style={[styles.content, item.role === "user" ? styles.userContent : styles.aiContent]}>
                {item.content || (isStreaming ? "..." : "")}
              </Text>
              {item.duration_ms && (
                <Text style={styles.meta}>{item.duration_ms}ms</Text>
              )}
            </View>
          )}
          onContentSizeChange={() => flatListRef.current?.scrollToEnd({ animated: true })}
        />

        {error && (
          <View style={styles.errorBanner}>
            <Text style={styles.errorText}>⚠ {error}</Text>
          </View>
        )}

        <View style={styles.inputRow}>
          <TextInput
            value={input}
            onChangeText={setInput}
            placeholder="اكتب رسالة..."
            placeholderTextColor="#666"
            style={styles.input}
            multiline
            editable={!isStreaming}
            onSubmitEditing={send}
            blurOnSubmit={false}
            returnKeyType="send"
          />
          <Pressable
            onPress={send}
            disabled={!input.trim() || isStreaming}
            style={[styles.sendButton, (!input.trim() || isStreaming) && styles.sendButtonDisabled]}
          >
            {isStreaming ? <ActivityIndicator color="#fff" /> : <Text style={styles.sendText}>➤</Text>}
          </Pressable>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  )
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#0a0a0f" },
  flex: { flex: 1 },
  list: { padding: 16, paddingBottom: 24 },
  bubble: {
    padding: 12,
    borderRadius: 12,
    marginBottom: 12,
    maxWidth: "85%",
  },
  userBubble: { backgroundColor: "#1e40af", alignSelf: "flex-end" },
  aiBubble: { backgroundColor: "#1f2937", alignSelf: "flex-start" },
  role: { fontSize: 11, fontWeight: "700", marginBottom: 4 },
  userRole: { color: "#bfdbfe" },
  aiRole: { color: "#a7f3d0" },
  content: { fontSize: 15, lineHeight: 22 },
  userContent: { color: "#fff" },
  aiContent: { color: "#e5e7eb" },
  meta: { fontSize: 10, color: "#9ca3af", marginTop: 6, textAlign: "right" },
  errorBanner: { backgroundColor: "#7f1d1d", padding: 8 },
  errorText: { color: "#fff", fontSize: 12, textAlign: "center" },
  inputRow: {
    flexDirection: "row",
    padding: 12,
    borderTopWidth: 1,
    borderTopColor: "#1f2937",
    alignItems: "flex-end",
  },
  input: {
    flex: 1,
    backgroundColor: "#1f2937",
    color: "#e5e7eb",
    padding: 10,
    borderRadius: 8,
    fontSize: 15,
    maxHeight: 120,
  },
  sendButton: {
    backgroundColor: "#10b981",
    width: 44,
    height: 44,
    borderRadius: 22,
    alignItems: "center",
    justifyContent: "center",
    marginLeft: 8,
  },
  sendButtonDisabled: { opacity: 0.4 },
  sendText: { color: "#fff", fontSize: 20, fontWeight: "700" },
})
