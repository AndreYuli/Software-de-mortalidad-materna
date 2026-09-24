import type { ReactNode } from 'react'
import { Heart } from 'lucide-react'

interface AuthCardProps {
  title: string
  subtitle: string
  children: ReactNode
  footer?: ReactNode
}

export default function AuthCard({ title, subtitle, children, footer }: AuthCardProps) {
  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-50 px-4 py-10">
      <div className="w-full max-w-md rounded-2xl bg-white p-8 shadow-lg">
        <div className="mb-6 flex flex-col items-center text-center">
          <div className="mb-3 flex size-14 items-center justify-center rounded-full bg-brand-magenta text-white">
            <Heart className="size-7" aria-hidden="true" />
          </div>
          <h1 className="text-2xl font-bold text-brand-deep">
            Vida<span className="text-brand-magenta">Materna</span>
          </h1>
        </div>

        <h2 className="text-xl font-semibold text-brand-deep">{title}</h2>
        <p className="mb-6 mt-1 text-sm text-slate-500">{subtitle}</p>

        {children}

        {footer && <p className="mt-6 text-center text-sm text-slate-600">{footer}</p>}
      </div>
    </main>
  )
}
