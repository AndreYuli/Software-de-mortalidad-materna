import { Sparkles } from 'lucide-react'

export interface ChartAiInsightProps {
  insight: string | null | undefined
}

export function ChartAiInsight({ insight }: ChartAiInsightProps) {
  if (!insight) return null

  return (
    <div className="mt-4 rounded-lg border border-brand-magenta/20 bg-brand-magenta/5 p-3">
      <span className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-brand-magenta">
        <Sparkles className="size-4" aria-hidden="true" />
        Lectura automatizada
      </span>
      <p className="mt-1 text-sm text-slate-700">{insight}</p>
    </div>
  )
}
