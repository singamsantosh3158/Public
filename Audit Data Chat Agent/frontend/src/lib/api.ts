import type { AuthStatus, ChatMessage, Conversation } from './types'

const BASE = '/api'

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`${res.status}: ${text}`)
  }
  return res.json()
}

export const api = {
  authStatus: () => req<AuthStatus>('/auth/status'),
  signIn: () => req<AuthStatus>('/auth/signin', { method: 'POST' }),
  signOut: () => req<AuthStatus>('/auth/signout', { method: 'POST' }),

  listConversations: () => req<Conversation[]>('/conversations'),
  newConversation: () => req<Conversation>('/conversations', { method: 'POST' }),
  getConversation: (id: string) => req<Conversation>(`/conversations/${id}`),
  renameConversation: (id: string, title: string) =>
    req<Conversation>(`/conversations/${id}`, {
      method: 'PATCH',
      body: JSON.stringify({ title }),
    }),
  deleteConversation: (id: string) => req<{ ok: boolean }>(`/conversations/${id}`, { method: 'DELETE' }),

  sendMessage: (conversationId: string, content: string) =>
    req<ChatMessage>(`/conversations/${conversationId}/messages`, {
      method: 'POST',
      body: JSON.stringify({ content }),
    }),
}
