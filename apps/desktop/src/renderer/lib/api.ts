const api = window.api

export interface ApiRequestOptions {
  method: string
  path: string
  body?: Record<string, unknown>
  headers?: Record<string, string>
}

export interface ApiResponse<T = unknown> {
  status: number
  data: T
  error?: string
}

export async function apiRequest<T = unknown>(options: ApiRequestOptions): Promise<ApiResponse<T>> {
  const result = await api.apiRequest({
    method: options.method,
    path: options.path,
    body: options.body ? JSON.stringify(options.body) : undefined,
    headers: options.headers
  })

  let parsedData: T
  try {
    parsedData = JSON.parse(result.data)
  } catch {
    parsedData = result.data as T
  }

  return {
    status: result.status,
    data: parsedData,
    error: result.status >= 400 ? result.data : undefined
  }
}

// Chat API
export const chatApi = {
  sendMessage: (message: string, sessionId?: string, voice?: boolean) =>
    apiRequest({
      method: 'POST',
      path: '/api/chat',
      body: { message, session_id: sessionId, voice: voice ?? true }
    }),

  getSessions: () =>
    apiRequest({ method: 'GET', path: '/api/chat/sessions' }),

  getSessionMessages: (sessionId: string) =>
    apiRequest({ method: 'GET', path: `/api/chat/sessions/${sessionId}/messages` }),

  searchSessions: (query: string) =>
    apiRequest({ method: 'POST', path: '/api/chat/search', body: { query } }),

  deleteSession: (sessionId: string) =>
    apiRequest({ method: 'DELETE', path: `/api/chat/sessions/${sessionId}` })
}

// Status API
export const statusApi = {
  getStatus: () =>
    apiRequest({ method: 'GET', path: '/api/status' }),

  getEngineHealth: () =>
    apiRequest({ method: 'GET', path: '/api/engine/health' })
}

// Knowledge API
export const knowledgeApi = {
  getCollections: () =>
    apiRequest({ method: 'GET', path: '/api/knowledge/collections' }),

  search: (query: string, collection?: string) =>
    apiRequest({
      method: 'POST',
      path: '/api/knowledge/search',
      body: { query, collection }
    }),

  add: (content: string, collection?: string, metadata?: Record<string, unknown>) =>
    apiRequest({
      method: 'POST',
      path: '/api/knowledge/add',
      body: { content, collection, metadata }
    })
}

// Memory API
export const memoryApi = {
  getStats: () =>
    apiRequest({ method: 'GET', path: '/api/memory/stats' }),

  search: (query: string) =>
    apiRequest({ method: 'POST', path: '/api/memory/search', body: { query } }),

  store: (content: string, category?: string) =>
    apiRequest({
      method: 'POST',
      path: '/api/memory/store',
      body: { content, category }
    })
}

// Tools API
export const toolsApi = {
  getAvailable: () =>
    apiRequest({ method: 'GET', path: '/api/tools/available' }),

  execute: (toolName: string, params: Record<string, unknown>) =>
    apiRequest({
      method: 'POST',
      path: '/api/tools/action',
      body: { tool: toolName, params }
    })
}

// Skills API
export const skillsApi = {
  getAll: () =>
    apiRequest({ method: 'GET', path: '/api/skills' })
}

// Models API
export const modelsApi = {
  getModels: () =>
    apiRequest({ method: 'POST', path: '/api/ollama/models' })
}

// Subagents API
export const subagentsApi = {
  spawn: (name: string, type: string, config?: Record<string, unknown>) =>
    apiRequest({
      method: 'POST',
      path: '/api/subagents/spawn',
      body: { name, type, config }
    }),

  list: () =>
    apiRequest({ method: 'GET', path: '/api/subagents' }),

  chat: (id: string, message: string) =>
    apiRequest({
      method: 'POST',
      path: `/api/subagents/${id}/chat`,
      body: { message }
    })
}

// MCP API
export const mcpApi = {
  getTools: () =>
    apiRequest({ method: 'GET', path: '/api/mcp/tools' }),

  addServer: (name: string, command: string, args: string[]) =>
    apiRequest({
      method: 'POST',
      path: '/api/mcp/add-server',
      body: { name, command, args }
    })
}

// Voice API
export const voiceApi = {
  synthesize: (text: string, language?: string) =>
    apiRequest({
      method: 'POST',
      path: '/api/voice/synthesize',
      body: { text, language }
    })
}

// Permissions API
export const permissionsApi = {
  getPermissions: () =>
    apiRequest({ method: 'GET', path: '/api/permissions' }),

  respond: (permissionId: string, allowed: boolean) =>
    apiRequest({
      method: 'POST',
      path: '/api/permissions/respond',
      body: { permission_id: permissionId, allowed }
    })
}

// Diagnostics API
export const diagnosticsApi = {
  getDiagnostics: () =>
    apiRequest({ method: 'GET', path: '/api/diagnostics' }),

  getPipelineLog: () =>
    apiRequest({ method: 'GET', path: '/api/engine/pipeline-log' })
}
