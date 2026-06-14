/**
 * [PHASE3] Adam Prism Mobile — Login screen
 */
import { useState } from "react"
import { View, Text, TextInput, Pressable, StyleSheet, Alert } from "react-native"
import { SafeAreaView } from "react-native-safe-area-context"
import { useAuthStore } from "../lib/auth"

export function LoginScreen() {
  const [isRegister, setIsRegister] = useState(false)
  const [email, setEmail] = useState("")
  const [username, setUsername] = useState("")
  const [password, setPassword] = useState("")
  const [loading, setLoading] = useState(false)
  const { login, register } = useAuthStore()

  const submit = async () => {
    if (loading) return
    setLoading(true)
    try {
      if (isRegister) {
        await register(email, username, password)
      } else {
        await login(username || email, password)
      }
    } catch (e: any) {
      Alert.alert("Error", e?.message || "Authentication failed")
    } finally {
      setLoading(false)
    }
  }

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.content}>
        <Text style={styles.title}>آدم بريزم</Text>
        <Text style={styles.subtitle}>Adam Prism</Text>

        {isRegister && (
          <TextInput
            value={email}
            onChangeText={setEmail}
            placeholder="email@example.com"
            placeholderTextColor="#666"
            autoCapitalize="none"
            keyboardType="email-address"
            style={styles.input}
          />
        )}
        <TextInput
          value={username}
          onChangeText={setUsername}
          placeholder={isRegister ? "username" : "username or email"}
          placeholderTextColor="#666"
          autoCapitalize="none"
          style={styles.input}
        />
        <TextInput
          value={password}
          onChangeText={setPassword}
          placeholder="password"
          placeholderTextColor="#666"
          secureTextEntry
          style={styles.input}
        />

        <Pressable onPress={submit} disabled={loading} style={[styles.button, loading && styles.disabled]}>
          <Text style={styles.buttonText}>
            {loading ? "..." : isRegister ? "Sign up" : "Sign in"}
          </Text>
        </Pressable>

        <Pressable onPress={() => setIsRegister(!isRegister)} style={styles.toggle}>
          <Text style={styles.toggleText}>
            {isRegister ? "Already have an account? Sign in" : "Don't have an account? Sign up"}
          </Text>
        </Pressable>
      </View>
    </SafeAreaView>
  )
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#0a0a0f" },
  content: { flex: 1, justifyContent: "center", padding: 24 },
  title: { color: "#fff", fontSize: 32, fontWeight: "700", textAlign: "center" },
  subtitle: { color: "#10b981", fontSize: 14, textAlign: "center", marginBottom: 32 },
  input: {
    backgroundColor: "#1f2937",
    color: "#e5e7eb",
    padding: 14,
    borderRadius: 8,
    fontSize: 15,
    marginBottom: 12,
  },
  button: {
    backgroundColor: "#10b981",
    padding: 14,
    borderRadius: 8,
    marginTop: 8,
  },
  disabled: { opacity: 0.5 },
  buttonText: { color: "#fff", textAlign: "center", fontSize: 16, fontWeight: "600" },
  toggle: { marginTop: 20 },
  toggleText: { color: "#9ca3af", textAlign: "center", fontSize: 13 },
})
