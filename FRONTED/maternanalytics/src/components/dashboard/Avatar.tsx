interface AvatarProps {
  letter: string
  className?: string
}

export function Avatar({ letter, className }: AvatarProps) {
  return (
    <div className={`avatar-okd ${className || ''}`} aria-hidden="true">
      {letter}
    </div>
  )
}
