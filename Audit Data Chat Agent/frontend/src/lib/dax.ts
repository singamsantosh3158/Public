import type { DaxCall } from './types'

export type FormattedResult =
  | { kind: 'error'; text: string }
  | { kind: 'empty'; text: string }
  | { kind: 'rows'; rows: Record<string, unknown>[] }

export function formatResult(call: DaxCall): FormattedResult {
  if (call.error) return { kind: 'error', text: call.error }
  if (!call.result) return { kind: 'empty', text: 'No rows returned.' }
  try {
    const rows = JSON.parse(call.result) as Record<string, unknown>[]
    if (rows.length === 0) return { kind: 'empty', text: 'No rows returned.' }
    return { kind: 'rows', rows }
  } catch {
    return { kind: 'empty', text: call.result }
  }
}
