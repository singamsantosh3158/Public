import { useEffect, useState } from 'react'
import { Composer } from './components/Composer'
import { Header } from './components/Header'
import { Sidebar } from './components/Sidebar'
import { Transcript } from './components/Transcript'
import { api } from './lib/api'
import type { AuthStatus, ChatMessage, Conversation } from './lib/types'

export default function App() {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [currentId, setCurrentId] = useState<string | null>(null)
  const [pending, setPending] = useState(false)

  const [auth, setAuth] = useState<AuthStatus>({ signedIn: false, user: null })
  const [authLoading, setAuthLoading] = useState(false)

  const [theme, setTheme] = useState<'light' | 'dark'>(() => {
    const stored = localStorage.getItem('theme')
    if (stored === 'light' || stored === 'dark') return stored
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
  })

  const current = conversations.find((c) => c.id === currentId) ?? null

  useEffect(() => {
    document.documentElement.classList.toggle('dark', theme === 'dark')
    localStorage.setItem('theme', theme)
  }, [theme])

  useEffect(() => {
    api.authStatus().then(setAuth).catch(() => {})
    Promise.all([api.listConversations(), api.newConversation()])
      .then(([past, fresh]) => {
        setConversations([fresh, ...past])
        setCurrentId(fresh.id)
      })
      .catch(() => {})
  }, [])

  const handleNewChat = async () => {
    const conv = await api.newConversation()
    setConversations((prev) => [conv, ...prev])
    setCurrentId(conv.id)
  }

  const handleSelect = async (id: string) => {
    const conv = await api.getConversation(id)
    setConversations((prev) => prev.map((c) => (c.id === id ? conv : c)))
    setCurrentId(id)
  }

  const handleRename = async (id: string, title: string) => {
    const updated = await api.renameConversation(id, title)
    setConversations((prev) => prev.map((c) => (c.id === id ? updated : c)))
  }

  const handleDelete = async (id: string) => {
    await api.deleteConversation(id)
    let remaining: Conversation[] = []
    setConversations((prev) => {
      remaining = prev.filter((c) => c.id !== id)
      return remaining
    })
    if (id === currentId) {
      if (remaining.length > 0) {
        setCurrentId(remaining[0].id)
      } else {
        const conv = await api.newConversation()
        setConversations([conv])
        setCurrentId(conv.id)
      }
    }
  }

  const handleSend = async (text: string) => {
    if (!currentId || !auth.signedIn) return
    const userMsg: ChatMessage = { id: crypto.randomUUID(), role: 'user', content: text }
    setConversations((prev) =>
      prev.map((c) => (c.id === currentId ? { ...c, messages: [...c.messages, userMsg] } : c)),
    )
    setPending(true)
    try {
      const reply = await api.sendMessage(currentId, text)
      setConversations((prev) =>
        prev.map((c) => {
          if (c.id !== currentId) return c
          const title = c.title ?? text
          return { ...c, title, messages: [...c.messages, reply] }
        }),
      )
    } catch (err) {
      const errorMsg: ChatMessage = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content:
          err instanceof Error && err.message.includes('401')
            ? '⚠️ Not signed in to Fabric. Click "Log in" at the top right first.'
            : `⚠️ Something went wrong: ${err instanceof Error ? err.message : String(err)}`,
      }
      setConversations((prev) =>
        prev.map((c) => (c.id === currentId ? { ...c, messages: [...c.messages, errorMsg] } : c)),
      )
    } finally {
      setPending(false)
    }
  }

  const handleSignIn = async () => {
    setAuthLoading(true)
    try {
      setAuth(await api.signIn())
    } finally {
      setAuthLoading(false)
    }
  }

  const handleSignOut = async () => {
    setAuth(await api.signOut())
  }

  return (
    <div className="flex h-full w-full bg-background text-foreground">
      <Sidebar
        collapsed={sidebarCollapsed}
        onToggleCollapsed={() => setSidebarCollapsed((v) => !v)}
        conversations={conversations.filter((c) => c.messages.length > 0)}
        currentId={currentId}
        onSelect={handleSelect}
        onNewChat={handleNewChat}
        onRename={handleRename}
        onDelete={handleDelete}
      />

      <div className="flex min-w-0 flex-1 flex-col">
        <Header
          title={current?.title ?? 'New chat'}
          auth={auth}
          authLoading={authLoading}
          onSignIn={handleSignIn}
          onSignOut={handleSignOut}
          theme={theme}
          onToggleTheme={() => setTheme((t) => (t === 'dark' ? 'light' : 'dark'))}
        />
        <Transcript
          messages={current?.messages ?? []}
          pending={pending}
          signedIn={auth.signedIn}
          onQuickStart={handleSend}
        />
        <Composer disabled={pending || !currentId} signedIn={auth.signedIn} onSend={handleSend} />
      </div>
    </div>
  )
}
