import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

/** Renders assistant Markdown (headers, bold, code, tables) with sizing that fits inline chat text. */
export function Markdown({ children }: { children: string }) {
  return (
    <div className="text-sm leading-relaxed [&>*:first-child]:mt-0 [&>*:last-child]:mb-0">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          p: ({ children }) => <p className="my-2">{children}</p>,
          h1: ({ children }) => <h3 className="mt-3 mb-1.5 text-base font-semibold">{children}</h3>,
          h2: ({ children }) => <h3 className="mt-3 mb-1.5 text-base font-semibold">{children}</h3>,
          h3: ({ children }) => (
            <h4 className="mt-3 mb-1.5 text-sm font-semibold">{children}</h4>
          ),
          strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
          ul: ({ children }) => <ul className="my-2 list-disc space-y-0.5 pl-5">{children}</ul>,
          ol: ({ children }) => <ol className="my-2 list-decimal space-y-0.5 pl-5">{children}</ol>,
          li: ({ children }) => <li>{children}</li>,
          code: ({ className, children, ...props }) => {
            const isBlock = /language-/.test(className ?? '')
            if (isBlock) {
              return (
                <code className={className} {...props}>
                  {children}
                </code>
              )
            }
            return (
              <code className="rounded bg-muted px-1 py-0.5 text-xs" {...props}>
                {children}
              </code>
            )
          },
          pre: ({ children }) => (
            <pre className="my-2 overflow-x-auto rounded-lg bg-muted p-2.5 text-xs whitespace-pre-wrap">
              {children}
            </pre>
          ),
          table: ({ children }) => (
            <div className="my-2 overflow-x-auto rounded-lg border border-border">
              <table className="w-full text-left text-xs">{children}</table>
            </div>
          ),
          thead: ({ children }) => <thead className="bg-muted">{children}</thead>,
          th: ({ children }) => (
            <th className="px-2.5 py-1.5 font-medium whitespace-nowrap">{children}</th>
          ),
          td: ({ children }) => <td className="px-2.5 py-1.5 whitespace-nowrap">{children}</td>,
          tr: ({ children }) => <tr className="border-t border-border">{children}</tr>,
          a: ({ children, href }) => (
            <a href={href} className="text-primary underline" target="_blank" rel="noreferrer">
              {children}
            </a>
          ),
        }}
      >
        {children}
      </ReactMarkdown>
    </div>
  )
}
