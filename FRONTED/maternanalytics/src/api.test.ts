import { describe, expect, it } from 'vitest'
import { API_URL } from './api'

describe('api', () => {
  it('expone una URL base http válida', () => {
    expect(API_URL).toMatch(/^https?:\/\//)
  })
})
