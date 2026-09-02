import ReactECharts from 'echarts-for-react'

export function Chart({ option }: { option: Record<string, unknown> }) {
  return (
    <div className="rounded-lg border border-border p-2">
      <ReactECharts option={option} style={{ height: 260, width: '100%' }} opts={{ renderer: 'svg' }} />
    </div>
  )
}
