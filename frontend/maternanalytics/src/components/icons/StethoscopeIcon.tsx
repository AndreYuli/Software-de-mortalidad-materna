import type { SVGProps } from 'react'

export function StethoscopeIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
      {...props}
    >
      <path stroke="none" d="M0 0h24v24H0z" fill="none" />
      <path d="M6 4h-1a2 2 0 0 0 -2 2v3.5a5.5 5.5 0 0 0 11 0v-3.5a2 2 0 0 0 -2 -2h-1" />
      <path d="M8 15a6 6 0 1 0 12 0v-3" />
      <path d="M11 3v2" />
      <path d="M6 3v2" />
      <path d="M18 10a2 2 0 1 0 4 0a2 2 0 1 0 -4 0" />
    </svg>
  )
}
