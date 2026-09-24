import type { ReactNode } from 'react'
import { AlertCircle, CheckCircle, Info } from 'lucide-react'

const VARIANTS = {
  error: { icon: AlertCircle, classes: 'border-red-200 bg-red-50 text-red-700', role: 'alert' },
  info: { icon: Info, classes: 'border-blue-200 bg-blue-50 text-blue-700', role: 'status' },
  success: { icon: CheckCircle, classes: 'border-green-200 bg-green-50 text-green-700', role: 'status' },
} as const

interface AuthNoticeProps {
  variant: keyof typeof VARIANTS
  children: ReactNode
}

export default function AuthNotice({ variant, children }: AuthNoticeProps) {
  const { icon: Icon, classes, role } = VARIANTS[variant]
  return (
    <div role={role} className={`flex items-start gap-2 rounded-lg border p-3 text-sm ${classes}`}>
      <Icon className="mt-0.5 size-4 shrink-0" aria-hidden="true" />
      <div>{children}</div>
    </div>
  )
}
