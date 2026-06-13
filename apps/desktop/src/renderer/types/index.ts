export interface Message {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: number
  tokens?: {
    prompt: number
    completion: number
    total: number
  }
  tools?: ToolCall[]
  attachments?: Attachment[]
  isStreaming?: boolean
}

export interface ToolCall {
  id: string
  name: string
  params: Record<string, unknown>
  status: 'pending' | 'running' | 'completed' | 'error'
  result?: string
  error?: string
  duration?: number
}

export interface Attachment {
  name: string
  type: string
  size: number
  url?: string
  data?: string
}

export interface Session {
  id: string
  title: string
  createdAt: number
  updatedAt: number
  messageCount: number
  lastMessage?: string
  model?: string
  pinned?: boolean
}

export interface Settings {
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

export interface KnowledgeCollection {
  id: string
  name: string
  documentCount: number
  createdAt: string
}

export interface KnowledgeSearchResult {
  content: string
  source: string
  score: number
  metadata?: Record<string, unknown>
}

export interface MemoryStats {
  totalMemories: number
  categories: Record<string, number>
  lastUpdated: string
}

export interface MemorySearchResult {
  id: string
  content: string
  category: string
  timestamp: string
  relevance: number
}

export interface ToolInfo {
  name: string
  description: string
  parameters: Record<string, unknown>
  enabled: boolean
  requiresPermission: boolean
}

export interface SkillInfo {
  id: string
  name: string
  description: string
  category: string
  enabled: boolean
}

export interface Subagent {
  id: string
  name: string
  type: string
  status: 'idle' | 'running' | 'completed' | 'error'
  createdAt: string
}

export interface MCPTool {
  name: string
  server: string
  description: string
  parameters: Record<string, unknown>
}

export interface MCPServer {
  name: string
  command: string
  args: string[]
  enabled: boolean
}

export interface PipelineEvent {
  type: 'step' | 'tool' | 'thinking' | 'error' | 'complete'
  data: Record<string, unknown>
  timestamp: string
}

export interface ServerStatus {
  status: 'online' | 'offline' | 'error'
  version?: string
  uptime?: number
  model?: string
}

export interface UpdateStatus {
  status: 'checking' | 'available' | 'downloading' | 'ready' | 'up-to-date' | 'error'
  version?: string
  percent?: number
  speed?: number
  message?: string
}

export type RightPanelView = 'files' | 'terminal' | 'memory' | 'knowledge' | 'tools' | 'pipeline' | 'subagents' | 'mcp' | 'none'
export type BottomPanelView = 'terminal' | 'logs' | 'pipeline' | 'none'

export interface AppState {
  // Sessions
  sessions: Session[]
  currentSessionId: string | null
  messages: Message[]

  // UI
  sidebarOpen: boolean
  rightPanelView: RightPanelView
  bottomPanelView: BottomPanelView
  settingsOpen: boolean
  commandPaletteOpen: boolean
  onboardingVisible: boolean

  // Status
  serverStatus: ServerStatus
  isStreaming: boolean
  updateStatus: UpdateStatus | null

  // Settings
  settings: Settings

  // Actions
  setSessions: (sessions: Session[]) => void
  addSession: (session: Session) => void
  removeSession: (id: string) => void
  setCurrentSession: (id: string | null) => void
  setMessages: (messages: Message[]) => void
  addMessage: (message: Message) => void
  updateMessage: (id: string, updates: Partial<Message>) => void
  setSidebarOpen: (open: boolean) => void
  setRightPanelView: (view: RightPanelView) => void
  setBottomPanelView: (view: BottomPanelView) => void
  setSettingsOpen: (open: boolean) => void
  setCommandPaletteOpen: (open: boolean) => void
  setOnboardingVisible: (visible: boolean) => void
  setServerStatus: (status: ServerStatus) => void
  setIsStreaming: (streaming: boolean) => void
  setUpdateStatus: (status: UpdateStatus | null) => void
  setSettings: (settings: Partial<Settings>) => void
  loadSessions: () => Promise<void>
  loadMessages: (sessionId: string) => Promise<void>
  sendMessage: (content: string, attachments?: Attachment[]) => Promise<void>
  deleteSession: (id: string) => Promise<void>
  createNewSession: () => void
  searchSessions: (query: string) => Promise<Session[]>
}
