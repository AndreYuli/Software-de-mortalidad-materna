interface AvatarProps {
  letter: string
  className?: string
}

export function Avatar({ letter, className = '' }: AvatarProps) {
  return (
    <div
      className={`flex size-9 shrink-0 items-center justify-center rounded-full bg-brand-deep text-sm font-semibold text-white ${className}`.trim()}
      aria-hidden="true"
    >
      {letter}
    </div>
  )
}
