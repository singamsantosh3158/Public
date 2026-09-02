import { ChevronDown, ChevronRight, Printer, Table2 } from 'lucide-react'
import { useEffect, useState } from 'react'
import { buildChartOption } from '../lib/chartOption'
import { formatResult } from '../lib/dax'
import { buildCardExport, downloadMarkdown } from '../lib/export'
import { wantsVisualization } from '../lib/intent'
import type { ChatMessage } from '../lib/types'
import { AuditMark, IconTile } from './brand'
import { Chart } from './Chart'
import { Markdown } from './Markdown'

const EXAMPLES = [
  'What is the current year sales?',
  'List the top 10 customers by revenue.',
  'Which vendors have the highest outstanding balance?',
  'What tables and measures are available in this model?',
]

const PENDING_STATUSES = [
  'Reading the data model…',
  'Retrieving the schema…',
  'Writing DAX…',
  'Running the query…',
]

function usePendingStatus(pending: boolean) {
  const [index, setIndex] = useState(0)

  useEffect(() => {
    if (!pending) {
      setIndex(0)
      return
    }
    const timer = setInterval(() => {
      setIndex((i) => (i + 1) % PENDING_STATUSES.length)
    }, 1600)
    return () => clearInterval(timer)
  }, [pending])

  return PENDING_STATUSES[index]
}

function ResultTable({ rows }: { rows: Record<string, unknown>[] }) {
  const columns = Object.keys(rows[0])
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left text-xs">
        <thead className="bg-muted">
          <tr>
            {columns.map((c) => (
              <th key={c} className="px-3 py-2 font-medium whitespace-nowrap">
                {c}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i} className="border-t border-border">
              {columns.map((c) => (
                <td key={c} className="px-3 py-2 whitespace-nowrap">
                  {String(row[c])}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

/** Export/Show-query action row shared by the result card and the chart fallback. */
function ResultActions({
  onExport,
  onToggleDax,
  daxOpen,
}: {
  onExport: () => void
  onToggleDax: () => void
  daxOpen: boolean
}) {
  return (
    <div className="flex items-center justify-end gap-4 text-xs text-muted-foreground">
      <button onClick={onExport} className="flex items-center gap-1.5 hover:text-foreground">
        <Printer size={13} />
        Export
      </button>
      <button onClick={onToggleDax} className="flex items-center gap-1.5 hover:text-foreground">
        {daxOpen ? <ChevronDown size={13} /> : <ChevronRight size={13} />}
        Show query
      </button>
    </div>
  )
}

/** Always-visible results: table/metrics/error — no query text. Renders a chart
 * instead of a table only when the question asked for a visualization, and never both.
 * A table result gets its own "Query result" card with export/show-query actions in the
 * footer; a chart result shows those same actions underneath instead. */
function ResultsSection({
  dax,
  question,
  onExport,
  onToggleDax,
  daxOpen,
}: {
  dax: NonNullable<ChatMessage['dax']>
  question: string
  onExport: () => void
  onToggleDax: () => void
  daxOpen: boolean
}) {
  const showChart = wantsVisualization(question)
  return (
    <div className="flex flex-col gap-3">
      {dax.map((call, i) => {
        const formatted = formatResult(call)
        return (
          <div key={i}>
            {formatted.kind === 'error' && (
              <div className="rounded-lg border border-destructive/30 bg-destructive/10 px-2.5 py-1.5 text-xs text-destructive">
                {formatted.text}
              </div>
            )}
            {formatted.kind === 'empty' && (
              <div className="text-xs text-muted-foreground">{formatted.text}</div>
            )}
            {formatted.kind === 'rows' &&
              (() => {
                const option = showChart ? buildChartOption(formatted.rows) : null
                if (option) {
                  return (
                    <div className="flex flex-col gap-2">
                      <Chart option={option} />
                      <ResultActions onExport={onExport} onToggleDax={onToggleDax} daxOpen={daxOpen} />
                    </div>
                  )
                }
                const cols = Object.keys(formatted.rows[0]).length
                return (
                  <div className="overflow-hidden rounded-xl border border-border">
                    <div className="flex items-center gap-1.5 border-b border-border bg-muted/50 px-3 py-2 text-xs font-medium">
                      <Table2 size={14} className="text-primary" />
                      Query result
                    </div>
                    <ResultTable rows={formatted.rows} />
                    <div className="flex items-center justify-between border-t border-border px-3 py-2 text-xs text-muted-foreground">
                      <span>
                        {formatted.rows.length} rows × {cols} cols
                      </span>
                      <ResultActions onExport={onExport} onToggleDax={onToggleDax} daxOpen={daxOpen} />
                    </div>
                  </div>
                )
              })()}
          </div>
        )
      })}
    </div>
  )
}

/** Toggle-gated: raw DAX query text only, no results. */
function DaxCodeSection({ dax }: { dax: NonNullable<ChatMessage['dax']> }) {
  return (
    <div className="mt-2 flex flex-col gap-3 rounded-xl border border-border bg-card p-3">
      {dax.map((call, i) => (
        <div key={i} className="flex flex-col gap-1.5">
          {dax.length > 1 && (
            <div className="text-xs font-semibold text-muted-foreground">DAX query {i + 1}</div>
          )}
          <pre className="overflow-x-auto rounded-lg bg-muted p-2.5 text-xs">
            <code>{call.query}</code>
          </pre>
        </div>
      ))}
    </div>
  )
}

interface TranscriptProps {
  messages: ChatMessage[]
  pending: boolean
  signedIn: boolean
  onQuickStart: (question: string) => void
}

export function Transcript({ messages, pending, signedIn, onQuickStart }: TranscriptProps) {
  const [expanded, setExpanded] = useState<Set<string>>(new Set())
  const pendingStatus = usePendingStatus(pending)

  const toggle = (id: string) => {
    setExpanded((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  if (messages.length === 0) {
    return (
      <div className="flex flex-1 items-center justify-center overflow-y-auto px-4">
        <div className="flex w-full max-w-md flex-col items-center gap-5 text-center">
          <div className="flex items-center gap-3">
            <IconTile size={56}>
              <AuditMark size={28} />
            </IconTile>
            <h1 className="text-xl font-semibold">Audit Chat Agent</h1>
          </div>
          {!signedIn && (
            <div className="rounded-lg border border-primary/30 bg-primary/10 px-3 py-2 text-xs text-primary">
              Sign in to Fabric (top right) before asking a question.
            </div>
          )}
          <div className="flex w-full flex-col gap-2">
            {EXAMPLES.map((q) => (
              <button
                key={q}
                onClick={() => onQuickStart(q)}
                disabled={!signedIn}
                className="rounded-xl border border-border bg-card px-4 py-3 text-left text-sm transition-colors hover:border-primary/50 hover:bg-accent/50 disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:border-border disabled:hover:bg-card"
              >
                {q}
              </button>
            ))}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="mx-auto flex max-w-2xl flex-col gap-5 px-4 py-6">
        {messages.map((m, i) => {
          const isOpen = expanded.has(m.id)
          const question = i > 0 ? messages[i - 1].content : ''
          return (
            <div key={m.id} className="flex flex-col gap-1.5">
              {m.role === 'user' ? (
                <div className="w-fit max-w-[85%] rounded-2xl bg-primary px-4 py-2 text-primary-foreground">
                  <Markdown>{m.content}</Markdown>
                </div>
              ) : (
                <div className="flex items-start gap-2">
                  <div className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary">
                    <AuditMark size={14} />
                  </div>
                  <div className="min-w-0 flex-1 space-y-1.5">
                    <Markdown>{m.content}</Markdown>
                    {m.analysisNote && (
                      <div className="text-xs text-muted-foreground">📝 {m.analysisNote}</div>
                    )}
                    {m.dax && m.dax.length > 0 && (
                      <>
                        <ResultsSection
                          dax={m.dax}
                          question={question}
                          onExport={() => {
                            const content = buildCardExport(question, m)
                            downloadMarkdown(`audit_qa_${m.id}.md`, content)
                          }}
                          onToggleDax={() => toggle(m.id)}
                          daxOpen={isOpen}
                        />
                        {isOpen && <DaxCodeSection dax={m.dax} />}
                      </>
                    )}
                  </div>
                </div>
              )}
            </div>
          )
        })}
        {pending && (
          <div className="flex flex-col gap-1.5">
            <div className="text-xs font-medium text-muted-foreground">{pendingStatus}</div>
            <div className="flex items-center gap-1 text-sm text-muted-foreground">
              <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-muted-foreground [animation-delay:-0.3s]" />
              <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-muted-foreground [animation-delay:-0.15s]" />
              <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-muted-foreground" />
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
