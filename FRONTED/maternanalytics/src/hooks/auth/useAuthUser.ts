import { useState } from 'react'

export function useAuthUser() {
  const [username] = useState(() => localStorage.getItem('username') || 'Usuario')
  const [email] = useState(() => localStorage.getItem('user_email') || '')
  const avatarLetter = (username || 'U').charAt(0).toUpperCase()

  return { username, email, avatarLetter }
}

