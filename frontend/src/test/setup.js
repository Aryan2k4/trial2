import '@testing-library/jest-dom'

// jsdom doesn't implement IntersectionObserver — several dashboard
// components (e.g. energy/SectionTabs.jsx) use it purely for
// scroll-spy UI, unrelated to what these tests assert. A minimal no-op
// stub is enough so mounting those components doesn't throw.
if (!global.IntersectionObserver) {
  global.IntersectionObserver = class {
    observe() {}
    unobserve() {}
    disconnect() {}
  }
}

// Same story for ResizeObserver — recharts' ResponsiveContainer uses it
// to size charts, which these tests don't assert pixel dimensions on.
if (!global.ResizeObserver) {
  global.ResizeObserver = class {
    observe() {}
    unobserve() {}
    disconnect() {}
  }
}
