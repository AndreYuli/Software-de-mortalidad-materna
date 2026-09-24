import { Loader2 } from 'lucide-react'

export function DashboardLoadingState() {
  return (
    <div role="status" className="flex min-h-[40vh] flex-col items-center justify-center gap-3 text-slate-600">
      <Loader2 className="size-8 animate-spin text-brand-magenta" aria-hidden="true" />
      <p>Generando panel estratégico...</p>
    </div>
  )
}
