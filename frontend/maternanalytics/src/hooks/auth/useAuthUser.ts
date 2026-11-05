import { useState } from 'react'

export function useAuthUser() {
  const [username] = useState(() => localStorage.getItem('username') || 'Usuario')
  const [email] = useState(() => localStorage.getItem('user_email') || '')
  const [secretaria] = useState(() => localStorage.getItem('user_secretaria') || '')
  const avatarLetter = (username.match(/[\p{L}\p{N}]/u)?.[0] ?? 'U').toUpperCase()

  return { username, email, avatarLetter, secretaria }
}

