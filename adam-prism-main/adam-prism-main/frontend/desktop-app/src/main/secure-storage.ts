/**
 * [PHASE1-SECURITY] Secure storage for sensitive data
 * Uses Electron's safeStorage API which encrypts data with OS-level keychain:
 * - macOS: Keychain
 * - Windows: DPAPI
 * - Linux: libsecret (gnome-keyring, kwallet)
 *
 * On platforms without safeStorage support, falls back to obfuscated storage.
 */
import { safeStorage } from 'electron'
import Store from 'electron-store'

interface SecureStoreSchema {
  apiKey: string  // Stored as base64-encoded encrypted bytes, or fallback obfuscated
  backendUrl: string
}

const secureStore = new Store<SecureStoreSchema>({
  name: 'secure-config',
  encryptionKey: undefined  // We use safeStorage for the actual encryption
})

/**
 * Save API key with OS-level encryption
 */
export function setApiKey(apiKey: string): boolean {
  try {
    if (safeStorage.isEncryptionAvailable()) {
      // Use OS-level encryption
      const encrypted = safeStorage.encryptString(apiKey)
      secureStore.set('apiKey', encrypted.toString('base64'))
      return true
    } else {
      // Fallback: store in a separate file with restricted permissions
      // Note: This is NOT secure on platforms without safeStorage
      console.warn(
        '[SECURITY] OS-level encryption not available. ' +
        'API key stored with basic obfuscation. ' +
        'Upgrade to macOS 10.14+, Windows 10+, or Linux with libsecret.'
      )
      // Simple base64 encoding as last-resort obfuscation
      secureStore.set('apiKey', Buffer.from(apiKey).toString('base64'))
      return true
    }
  } catch (err) {
    console.error('Failed to save API key securely:', err)
    return false
  }
}

/**
 * Retrieve and decrypt API key
 */
export function getApiKey(): string {
  try {
    const stored = secureStore.get('apiKey', '')
    if (!stored) return ''

    if (safeStorage.isEncryptionAvailable()) {
      // Decrypt with OS keychain
      const encrypted = Buffer.from(stored, 'base64')
      return safeStorage.decryptString(encrypted)
    } else {
      // Fallback: decode base64
      return Buffer.from(stored, 'base64').toString('utf-8')
    }
  } catch (err) {
    console.error('Failed to retrieve API key:', err)
    return ''
  }
}

/**
 * Clear stored API key
 */
export function clearApiKey(): void {
  secureStore.delete('apiKey')
}

/**
 * Check if encryption is available on this system
 */
export function isSecureStorageAvailable(): boolean {
  return safeStorage.isEncryptionAvailable()
}
