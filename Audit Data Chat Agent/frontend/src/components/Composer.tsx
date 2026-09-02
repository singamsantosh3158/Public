import { ArrowUp, Mic, Square } from 'lucide-react'
import { useState, type KeyboardEvent } from 'react'
import { useSpeechRecognition } from '../lib/useSpeechRecognition'

interface ComposerProps {
  disabled: boolean
  signedIn: boolean
  onSend: (text: string) => void
}

export function Composer({ disabled, signedIn, onSend }: ComposerProps) {
  const [value, setValue] = useState('')
  const blocked = disabled || !signedIn

  const { isListening, isSupported, toggle: toggleVoice } = useSpeechRecognition((finalText) => {
    setValue((prev) => (prev ? `${prev} ${finalText}` : finalText))
  })

  const submit = () => {
    const text = value.trim()
    if (!text || blocked) return
    onSend(text)
    setValue('')
  }

  const onKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      submit()
    }
  }

  return (
    <div className="shrink-0 border-t border-border bg-background px-4 py-3">
      <div className="mx-auto flex max-w-2xl items-end gap-2 rounded-2xl border border-border bg-card px-3 py-2 shadow-sm">
        <textarea
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={onKeyDown}
          disabled={!signedIn}
          rows={1}
          placeholder={
            signedIn
              ? isListening
                ? 'Listening...'
                : 'Ask about your Fabric semantic model...'
              : 'Sign in to Fabric to start chatting...'
          }
          className="max-h-40 flex-1 resize-none bg-transparent py-1.5 text-sm outline-none placeholder:text-muted-foreground disabled:cursor-not-allowed"
        />
        {isSupported && (
          <button
            onClick={toggleVoice}
            disabled={!signedIn}
            title={isListening ? 'Stop voice input' : 'Voice input'}
            className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-primary text-sm text-primary-foreground transition-opacity disabled:cursor-not-allowed disabled:opacity-30 ${
              isListening ? 'opacity-70' : 'hover:opacity-90'
            }`}
            aria-label={isListening ? 'Stop voice input' : 'Voice input'}
          >
            {isListening ? <Square size={14} /> : <Mic size={16} />}
          </button>
        )}
        <button
          onClick={submit}
          disabled={blocked || !value.trim()}
          className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-primary text-primary-foreground transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-30"
          aria-label="Send"
        >
          <ArrowUp size={16} />
        </button>
      </div>
      <div className="mx-auto mt-1.5 max-w-2xl text-center text-[11px] text-muted-foreground">
        {signedIn ? 'Enter to send · Shift+Enter for a new line' : 'Sign in required to ask questions'}
      </div>
    </div>
  )
}
