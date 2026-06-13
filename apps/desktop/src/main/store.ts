import Store from 'electron-store'

interface StoreSchema {
  backendUrl: string
  apiKey: string
  isLocal: boolean
  theme: 'dark' | 'light' | 'system'
  language: 'ar' | 'en'
  onboardingComplete: boolean
  notificationsEnabled: boolean
  model: string
  windowBounds: { x: number; y: number; width: number; height: number }
  sidebarWidth: number
  rightPanelWidth: number
  bottomPanelHeight: number
  voiceEnabled: boolean
  voiceSttLanguage: string
  voiceTtsLanguage: string
}

const defaults: StoreSchema = {
  backendUrl: 'http://localhost:8000',
  apiKey: '',
  isLocal: true,
  theme: 'dark',
  language: 'ar',
  onboardingComplete: false,
  notificationsEnabled: true,
  model: 'adam',
  windowBounds: { x: 100, y: 100, width: 1400, height: 900 },
  sidebarWidth: 280,
  rightPanelWidth: 360,
  bottomPanelHeight: 220,
  voiceEnabled: true,
  voiceSttLanguage: 'ar',
  voiceTtsLanguage: 'ar'
}

export const store = new Store<StoreSchema>({ defaults })

export function getStoreValue<K extends keyof StoreSchema>(key: K): StoreSchema[K] {
  return store.get(key)
}

export function setStoreValue<K extends keyof StoreSchema>(key: K, value: StoreSchema[K]): void {
  store.set(key, value)
}

export function getAllSettings(): StoreSchema {
  return {
    backendUrl: store.get('backendUrl'),
    apiKey: store.get('apiKey'),
    isLocal: store.get('isLocal'),
    theme: store.get('theme'),
    language: store.get('language'),
    onboardingComplete: store.get('onboardingComplete'),
    notificationsEnabled: store.get('notificationsEnabled'),
    model: store.get('model'),
    windowBounds: store.get('windowBounds'),
    sidebarWidth: store.get('sidebarWidth'),
    rightPanelWidth: store.get('rightPanelWidth'),
    bottomPanelHeight: store.get('bottomPanelHeight'),
    voiceEnabled: store.get('voiceEnabled'),
    voiceSttLanguage: store.get('voiceSttLanguage'),
    voiceTtsLanguage: store.get('voiceTtsLanguage')
  }
}
