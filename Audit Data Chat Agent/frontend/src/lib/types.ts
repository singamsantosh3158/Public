export interface DaxCall {
  query: string
  result: string | null
  error: string | null
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  dax?: DaxCall[]
  analysisNote?: string | null
}

export interface Conversation {
  id: string
  title: string | null
  messages: ChatMessage[]
}

export interface DeviceCode {
  verificationUri: string
  userCode: string
}

export interface AuthStatus {
  signedIn: boolean
  user: string | null
  deviceCode?: DeviceCode | null
}
