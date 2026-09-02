/**
 * Builds an Apache ECharts option from DAX result rows. Mirrors src/viz.py's rules:
 * sequential single-hue for plain magnitude, the fixed 8-hue categorical order only for
 * genuinely multiple series, never a rainbow, never dual-axis, data labels on marks,
 * axis/hover tooltip always on.
 */

// Fixed categorical hue order (validated for CVD-safety) - never cycle/generate hues.
const CATEGORICAL_PALETTE = [
  '#2a78d6', // blue
  '#eb6834', // orange
  '#1baf7a', // aqua
  '#eda100', // yellow
  '#e87ba4', // magenta
  '#008300', // green
  '#4a3aa7', // violet
  '#e34948', // red
]
const SEQUENTIAL_BLUE = '#2a78d6'
const GRIDLINE = '#e1e0d9'
const MUTED_INK = '#898781'
const PRIMARY_INK = '#0b0b0b'

type Row = Record<string, unknown>

function isNumeric(v: unknown): boolean {
  if (typeof v === 'number') return Number.isFinite(v)
  if (typeof v === 'string' && v.trim() !== '') return !Number.isNaN(Number(v))
  return false
}

function isDateColumn(rows: Row[], col: string): boolean {
  return rows.every((r) => {
    const v = r[col]
    if (v == null) return false
    if (isNumeric(v)) return false
    return !Number.isNaN(Date.parse(String(v)))
  })
}

export function buildChartOption(rows: Row[]): Record<string, unknown> | null {
  if (!rows || rows.length < 2) return null
  const columns = Object.keys(rows[0])
  if (columns.length < 2) return null

  const numericCols = columns.filter((c) => rows.every((r) => isNumeric(r[c])))
  const otherCols = columns.filter((c) => !numericCols.includes(c))
  if (numericCols.length === 0 || otherCols.length === 0) return null

  const dateCol = otherCols.find((c) => isDateColumn(rows, c))
  const categoryCol = dateCol ?? otherCols[0]

  const sorted = [...rows].sort((a, b) => {
    const av = a[categoryCol]
    const bv = b[categoryCol]
    if (dateCol) return Date.parse(String(av)) - Date.parse(String(bv))
    return String(av).localeCompare(String(bv))
  })

  const categories = sorted.map((r) => String(r[categoryCol]))
  const base = {
    backgroundColor: 'transparent',
    textStyle: { color: PRIMARY_INK, fontFamily: 'system-ui, -apple-system, "Segoe UI", sans-serif' },
    grid: { left: 8, right: 16, top: numericCols.length > 1 ? 36 : 24, bottom: 8, containLabel: true },
    xAxis: {
      type: 'category',
      data: categories,
      axisLine: { lineStyle: { color: MUTED_INK } },
      axisLabel: { color: MUTED_INK, fontSize: 11 },
      axisTick: { show: false },
    },
    yAxis: {
      type: 'value',
      axisLine: { show: false },
      axisLabel: { color: MUTED_INK, fontSize: 11 },
      splitLine: { lineStyle: { color: GRIDLINE } },
    },
    tooltip: { trigger: 'axis' },
  }

  if (numericCols.length === 1) {
    const measure = numericCols[0]
    const values = sorted.map((r) => Number(r[measure]))
    if (dateCol) {
      return {
        ...base,
        series: [
          {
            name: measure,
            type: 'line',
            data: values,
            color: SEQUENTIAL_BLUE,
            lineStyle: { width: 2, color: SEQUENTIAL_BLUE },
            itemStyle: { color: SEQUENTIAL_BLUE },
            symbolSize: 7,
            label: { show: true, position: 'top', fontSize: 10, color: PRIMARY_INK },
          },
        ],
      }
    }
    return {
      ...base,
      series: [
        {
          name: measure,
          type: 'bar',
          data: values,
          color: SEQUENTIAL_BLUE,
          barMaxWidth: 40,
          label: { show: true, position: 'top', fontSize: 10, color: PRIMARY_INK },
        },
      ],
    }
  }

  const measures = numericCols.slice(0, 8)
  return {
    ...base,
    legend: { top: 0, textStyle: { color: MUTED_INK, fontSize: 11 } },
    series: measures.map((measure, i) => ({
      name: measure,
      type: 'bar',
      data: sorted.map((r) => Number(r[measure])),
      color: CATEGORICAL_PALETTE[i % CATEGORICAL_PALETTE.length],
      barMaxWidth: 28,
      label: { show: true, position: 'top', fontSize: 9, color: PRIMARY_INK },
    })),
  }
}
