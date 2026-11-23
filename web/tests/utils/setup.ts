import { cleanup } from '@testing-library/react'
import { afterAll, afterEach, beforeAll } from 'vitest'
import '@testing-library/jest-dom/vitest'
import { installLayoutShims } from 'strata-react/testing'
import { resetMock, server } from './server'

// jsdom does no layout and has no ResizeObserver: Strata's shims give measuring components (tables,
// virtual lists) a box to render into, and a working localStorage where Node 25+ hides jsdom's. Real layout is checked by the visual suite in Chromium.
installLayoutShims()

// An endpoint without a handler fails the test, so a screen cannot quietly depend on a real server.
beforeAll(() => server.listen({ onUnhandledFrame: 'error' }))
afterEach(() => {
  cleanup()
  server.resetHandlers()
  resetMock()
  document.documentElement.classList.remove('dark')
})
afterAll(() => server.close())
