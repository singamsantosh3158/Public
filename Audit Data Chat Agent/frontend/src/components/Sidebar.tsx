import { MessageSquare, PanelLeftClose, PanelLeftOpen, Pencil, Plus, Trash2 } from 'lucide-react'
import { useState } from 'react'
import type { Conversation } from '../lib/types'
import { AuditMark } from './brand'

interface SidebarProps {
  collapsed: boolean
  onToggleCollapsed: () => void
  conversations: Conversation[]
  currentId: string | null
  onSelect: (id: string) => void
  onNewChat: () => void
  onRename: (id: string, title: string) => void
  onDelete: (id: string) => void
}

export function Sidebar({
  collapsed,
  onToggleCollapsed,
  conversations,
  currentId,
  onSelect,
  onNewChat,
  onRename,
  onDelete,
}: SidebarProps) {
  const [editingId, setEditingId] = useState<string | null>(null)
  const [editValue, setEditValue] = useState('')

  const startEditing = (c: Conversation) => {
    setEditingId(c.id)
    setEditValue(c.title ?? '')
  }

  const commitEdit = () => {
    if (editingId && editValue.trim()) {
      onRename(editingId, editValue.trim())
    }
    setEditingId(null)
  }

  if (collapsed) {
    return (
      <div className="flex h-full w-14 shrink-0 flex-col items-center gap-3 border-r border-border bg-card py-3">
        <button
          onClick={onToggleCollapsed}
          className="flex h-9 w-9 items-center justify-center rounded-lg text-muted-foreground hover:bg-accent hover:text-foreground"
          aria-label="Expand sidebar"
        >
          <PanelLeftOpen size={18} />
        </button>
        <button
          onClick={onNewChat}
          className="flex h-9 w-9 items-center justify-center rounded-lg text-muted-foreground hover:bg-accent hover:text-foreground"
          aria-label="New chat"
        >
          <Plus size={18} />
        </button>
      </div>
    )
  }

  return (
    <div className="flex h-full w-64 shrink-0 flex-col border-r border-border bg-card">
      <div className="flex items-center justify-between gap-2 p-3">
        <div className="flex items-center gap-2 px-1">
          <AuditMark size={18} />
          <span className="text-sm font-semibold">Audit Data Chat</span>
        </div>
        <button
          onClick={onToggleCollapsed}
          className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-muted-foreground hover:bg-accent hover:text-foreground"
          aria-label="Collapse sidebar"
        >
          <PanelLeftClose size={16} />
        </button>
      </div>

      <div className="px-3">
        <button
          onClick={onNewChat}
          className="flex w-full items-center gap-2 rounded-xl border border-border bg-card px-3 py-2 text-sm font-medium transition-colors hover:border-primary/50 hover:bg-accent/50"
        >
          <Plus size={16} />
          New chat
        </button>
      </div>

      <div className="mt-4 flex-1 overflow-y-auto px-3">
        {conversations.length > 0 && (
          <div className="mb-1 px-1 text-xs font-semibold tracking-wide text-muted-foreground uppercase">
            Recent
          </div>
        )}
        <div className="flex flex-col gap-0.5 pb-3">
          {conversations.map((c) => (
            <div
              key={c.id}
              className={`group flex items-center gap-1 rounded-lg pr-1 transition-colors hover:bg-accent/50 ${
                c.id === currentId ? 'bg-accent text-foreground' : 'text-muted-foreground'
              }`}
            >
              {editingId === c.id ? (
                <input
                  autoFocus
                  value={editValue}
                  onChange={(e) => setEditValue(e.target.value)}
                  onBlur={commitEdit}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') commitEdit()
                    if (e.key === 'Escape') setEditingId(null)
                  }}
                  className="min-w-0 flex-1 rounded-md bg-background px-2 py-1 text-sm outline-none ring-1 ring-primary/50"
                />
              ) : (
                <button
                  onClick={() => onSelect(c.id)}
                  className="flex min-w-0 flex-1 items-center gap-2 truncate px-2 py-1.5 text-left text-sm"
                >
                  <MessageSquare size={14} className="shrink-0" />
                  <span className="truncate">{c.title ?? 'Untitled chat'}</span>
                </button>
              )}

              {editingId !== c.id && (
                <div className="flex shrink-0 gap-0.5 opacity-0 transition-opacity group-hover:opacity-100">
                  <button
                    onClick={() => startEditing(c)}
                    className="flex h-6 w-6 items-center justify-center rounded-md hover:bg-background hover:text-foreground"
                    aria-label="Rename conversation"
                  >
                    <Pencil size={12} />
                  </button>
                  <button
                    onClick={() => onDelete(c.id)}
                    className="flex h-6 w-6 items-center justify-center rounded-md hover:bg-background hover:text-destructive"
                    aria-label="Delete conversation"
                  >
                    <Trash2 size={12} />
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
