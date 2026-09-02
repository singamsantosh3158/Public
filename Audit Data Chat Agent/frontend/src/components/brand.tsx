/** Audit Chat Agent brand mark: a bar chart with a magnifying-glass accent. */
export function AuditMark({ size = 20 }: { size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      <rect x="3" y="13" width="3.5" height="8" rx="1" fill="var(--color-primary)" />
      <rect x="8.25" y="8" width="3.5" height="13" rx="1" fill="var(--color-primary)" />
      <rect x="13.5" y="11" width="3.5" height="10" rx="1" fill="var(--color-primary)" />
      <circle cx="17.5" cy="6.5" r="2.75" stroke="var(--color-primary)" strokeWidth="1.6" />
      <line
        x1="19.4"
        y1="8.4"
        x2="21"
        y2="10"
        stroke="var(--color-primary)"
        strokeWidth="1.6"
        strokeLinecap="round"
      />
    </svg>
  )
}

/** Soft rounded-square icon tile, matching the tinted-square-behind-an-icon motif used app-wide. */
export function IconTile({
  children,
  size = 40,
}: {
  children: React.ReactNode
  size?: number
}) {
  return (
    <div
      className="flex shrink-0 items-center justify-center rounded-xl bg-primary/10"
      style={{ width: size, height: size }}
    >
      {children}
    </div>
  )
}
