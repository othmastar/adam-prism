/**
 * [PHASE3] Adam Prism Mobile — App entry
 */
import { useEffect } from "react"
import { View, ActivityIndicator, StyleSheet } from "react-native"
import { SafeAreaProvider } from "react-native-safe-area-context"
import { useAuthStore } from "./lib/auth"
import { LoginScreen } from "./screens/LoginScreen"
import { ChatScreen } from "./screens/ChatScreen"

export default function App() {
  const { isAuthenticated, isLoading, loadStoredAuth, logout } = useAuthStore()

  useEffect(() => {
    loadStoredAuth()
  }, [])

  if (isLoading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator color="#10b981" size="large" />
      </View>
    )
  }

  return (
    <SafeAreaProvider>
      {isAuthenticated ? <ChatScreen /> : <LoginScreen />}
    </SafeAreaProvider>
  )
}

const styles = StyleSheet.create({
  center: { flex: 1, backgroundColor: "#0a0a0f", justifyContent: "center", alignItems: "center" },
})
