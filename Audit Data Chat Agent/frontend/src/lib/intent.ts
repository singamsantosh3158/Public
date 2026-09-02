const VISUALIZATION_RE = /\b(chart|graph|plot|visuali[sz]e|visuali[sz]ation|diagram)\b/i

export function wantsVisualization(question: string): boolean {
  return VISUALIZATION_RE.test(question)
}
