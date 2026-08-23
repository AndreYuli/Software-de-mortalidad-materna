import { useState } from 'react'

export function useAuthUser() {
  const [username] = useState(() => localStorage.getItem('username') || 'Usuario')
  const avatarLetter = username.charAt(0).toUpperCase()

  return { username, avatarLetter }
}
