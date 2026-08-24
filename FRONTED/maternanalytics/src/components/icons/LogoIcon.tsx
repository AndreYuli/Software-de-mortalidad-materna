import type { SVGProps } from 'react'

export function LogoIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
  return (
    <svg
      viewBox="0 0 64 64"
      className={className}
      aria-hidden="true"
      {...props}
    >
      <circle cx="32" cy="32" r="26" fill="none" stroke="currentColor" strokeWidth="2.5" />
      <rect x="20" y="34" width="6" height="12" rx="1.5" fill="currentColor" opacity="0.55" />
      <rect x="29" y="28" width="6" height="18" rx="1.5" fill="currentColor" opacity="0.55" />
      <rect x="38" y="20" width="6" height="26" rx="1.5" fill="currentColor" opacity="0.55" />
      <path
        d="M23 34 L32 28 L41 20"
        fill="none"
        stroke="var(--pink-500)"
        strokeWidth="2.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <circle cx="41" cy="20" r="3" fill="var(--pink-500)" />
    </svg>
  )
}

export default LogoIcon
