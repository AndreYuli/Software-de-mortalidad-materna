import type { SVGProps } from 'react'

export function SendIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <polyline points="22 2 11 13" />
      <polygon points="22 2 15 22 11 13 2 9 22 2" />
    </svg>
  )
}
