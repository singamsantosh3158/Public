import { LogIn, LogOut, Moon, Sun, User } from 'lucide-react'
import { useState } from 'react'
import type { AuthStatus } from '../lib/types'

interface HeaderProps {
  title: string
  auth: AuthStatus
  authLoading: boolean
  onSignIn: () => void
  onSignOut: () => void
  theme: 'light' | 'dark'
  onToggleTheme: () => void
}

export function Header({ title, auth, authLoading, onSignIn, onSignOut, theme, onToggleTheme }: HeaderProps) {
  const [menuOpen, setMenuOpen] = useState(false)

  return (
    <div className="flex h-14 shrink-0 items-center justify-between border-b border-border px-4">
      <div className="flex items-center gap-2 text-sm">
        <span className="font-semibold text-primary">Audit Chat Agent</span>
        <span className="text-muted-foreground">|</span>
        <span className="text-muted-foreground">{title}</span>
      </div>

      <div className="flex items-center gap-2">
        <button
          onClick={onToggleTheme}
          title={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
          aria-label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
          className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-border bg-white text-blue-500 transition-colors hover:border-primary/50 hover:bg-accent/50"
        >
          {theme === 'dark' ? <Sun size={16} /> : <Moon size={16} />}
        </button>

        <div className="relative">
          {auth.signedIn ? (
            <button
              onClick={() => setMenuOpen((v) => !v)}
              className="flex items-center gap-1.5 rounded-lg border border-border bg-white px-2.5 py-1.5 text-xs font-medium text-blue-500 transition-colors hover:border-primary/50 hover:bg-accent/50"
            >
              <User size={14} />
              {auth.user ?? 'Signed in'}
            </button>
          ) : (
            <button
              onClick={onSignIn}
              disabled={authLoading}
              className="flex items-center gap-1.5 rounded-lg border border-primary/40 px-2.5 py-1.5 text-xs font-medium text-primary transition-colors hover:bg-primary/10 disabled:opacity-50"
            >
              <LogIn size={14} />
              {authLoading ? 'Signing in…' : 'Log in'}
            </button>
          )}

          {menuOpen && auth.signedIn && (
            <div className="absolute right-0 top-full z-10 mt-1 w-44 rounded-xl border border-border bg-popover p-1 shadow-md">
              <div className="px-2 py-1.5 text-xs text-muted-foreground">
                Signed in as <span className="font-medium text-foreground">{auth.user}</span>
              </div>
              <button
                onClick={() => {
                  setMenuOpen(false)
                  onSignOut()
                }}
                className="flex w-full items-center gap-1.5 rounded-lg px-2 py-1.5 text-left text-sm hover:bg-accent"
              >
                <LogOut size={14} />
                Sign out
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
