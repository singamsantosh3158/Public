import type { ChatMessage } from './types'

export function buildCardExport(question: string, message: ChatMessage): string {
  const lines = ['# Audit Chat Agent - Q&A Export', `_Exported ${new Date().toISOString()}_`, '']
  lines.push(`**You**: ${question}`)
  lines.push(`**Agent**: ${message.content}`)
  ;(message.dax ?? []).forEach((call, i) => {
    lines.push(`\n<details><summary>DAX query ${i + 1}</summary>\n`)
    lines.push(`\`\`\`dax\n${call.query}\n\`\`\``)
    if (call.error) {
      lines.push(`\nError: ${call.error}`)
    } else {
      lines.push(`\nResult:\n\`\`\`json\n${call.result}\n\`\`\``)
    }
    lines.push('</details>')
  })
  return lines.join('\n')
}

export function downloadMarkdown(filename: string, content: string): void {
  const blob = new Blob([content], { type: 'text/markdown' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(url)
}
