import '@testing-library/jest-dom/vitest'
import 'vitest-canvas-mock'

// jsdom does not implement ResizeObserver, but Chart.js's responsive plugin
// requires it to be present at chart-construction time.
if (typeof globalThis.ResizeObserver === 'undefined') {
  globalThis.ResizeObserver = class ResizeObserver {
    observe() {}
    unobserve() {}
    disconnect() {}
  }
}
