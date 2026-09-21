import type { ReactNode } from 'react'
import { ChartAiInsight } from './ChartAiInsight'

export interface ChartCardProps {
  title: string
  eyebrow?: string
  description?: string
  /** Lectura automatizada bajo la gráfica; sin texto no se muestra nada. */
  insight?: string | null
  children: ReactNode
}

export function ChartCard({ title, eyebrow, description, insight, children }: ChartCardProps) {
  return (
    <article className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="mb-4">
        {eyebrow && (
          <span className="block text-xs font-semibold uppercase tracking-wider text-brand-magenta">{eyebrow}</span>
        )}
        <h3 className="text-lg font-semibold text-brand-deep">{title}</h3>
        {description && <p className="mt-1 text-sm text-slate-500">{description}</p>}
      </div>
      {children}
      <ChartAiInsight insight={insight} />
    </article>
  )
}
