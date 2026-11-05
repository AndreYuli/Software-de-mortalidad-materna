import { afterEach, describe, expect, it } from 'vitest'
import { renderHook } from '@testing-library/react'
import { useAuthUser } from './useAuthUser'

describe('useAuthUser', () => {
  afterEach(() => {
    localStorage.clear()
  })

  it.each([
    ['Andrea', 'A'],
    ['ángela', 'Á'],
    ['<img src=x>', 'I'],
    ['<<< >>>', 'U'],
  ])('usa la primera letra o número de %s como inicial (%s)', (username, expected) => {
    localStorage.setItem('username', username)
    const { result } = renderHook(() => useAuthUser())
    expect(result.current.avatarLetter).toBe(expected)
  })

  it("usa 'U' cuando no hay username guardado", () => {
    const { result } = renderHook(() => useAuthUser())
    expect(result.current.username).toBe('Usuario')
    expect(result.current.avatarLetter).toBe('U')
  })
})
