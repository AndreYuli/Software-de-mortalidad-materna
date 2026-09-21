import { useState } from 'react'
import { Eye, EyeOff, type LucideIcon } from 'lucide-react'
import type { UseFormRegisterReturn } from 'react-hook-form'

interface AuthFieldProps {
  id: string
  label: string
  icon: LucideIcon
  type?: 'text' | 'email' | 'password'
  placeholder?: string
  error?: string
  registration: UseFormRegisterReturn
}

export default function AuthField({
  id,
  label,
  icon: Icon,
  type = 'text',
  placeholder,
  error,
  registration,
}: AuthFieldProps) {
  const [visible, setVisible] = useState(false)
  const isPassword = type === 'password'
  const inputType = isPassword && visible ? 'text' : type
  const errorId = `${id}-error`

  return (
    <div>
      <label htmlFor={id} className="mb-1 block text-sm font-medium text-slate-700">
        {label}
      </label>
      <div className="relative">
        <Icon
          className="pointer-events-none absolute left-3 top-1/2 size-5 -translate-y-1/2 text-slate-400"
          aria-hidden="true"
        />
        <input
          id={id}
          type={inputType}
          placeholder={placeholder}
          required
          aria-invalid={error ? true : undefined}
          aria-describedby={error ? errorId : undefined}
          className={`w-full rounded-lg border bg-white py-2.5 pl-10 text-slate-900 outline-none transition focus:ring-2 focus:ring-brand-magenta/30 ${
            isPassword ? 'pr-11' : 'pr-3'
          } ${error ? 'border-red-500' : 'border-slate-300 focus:border-brand-magenta'}`}
          {...registration}
        />
        {isPassword && (
          <button
            type="button"
            aria-label={visible ? 'Ocultar' : 'Mostrar'}
            aria-pressed={visible}
            onClick={() => setVisible((v) => !v)}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-brand-violet"
          >
            {visible ? <EyeOff className="size-5" aria-hidden="true" /> : <Eye className="size-5" aria-hidden="true" />}
          </button>
        )}
      </div>
      {error && (
        <p id={errorId} className="mt-1 text-sm text-red-600">
          {error}
        </p>
      )}
    </div>
  )
}
