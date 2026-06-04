import { describe, expect, it, vi, beforeEach } from 'vitest'
import { api, onAuthExpired, setStoredAccessToken } from './api.js'

describe('api auth expiry handling', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('notifies listeners when an authenticated request receives 401', async () => {
    const listener = vi.fn()
    const unsubscribe = onAuthExpired(listener)
    setStoredAccessToken('expired-token')

    await expect(
      api.get('/users/me/', {
        adapter: (config) => Promise.reject({ config, response: { status: 401 } }),
      }),
    ).rejects.toMatchObject({ response: { status: 401 } })

    expect(listener).toHaveBeenCalledTimes(1)
    unsubscribe()
  })

  it('does not notify listeners when an unauthenticated request receives 401', async () => {
    const listener = vi.fn()
    const unsubscribe = onAuthExpired(listener)

    await expect(
      api.get('/users/login/', {
        adapter: (config) => Promise.reject({ config, response: { status: 401 } }),
      }),
    ).rejects.toMatchObject({ response: { status: 401 } })

    expect(listener).not.toHaveBeenCalled()
    unsubscribe()
  })
})
