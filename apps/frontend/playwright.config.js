import { defineConfig } from '@playwright/test'

export default defineConfig({
  testDir: './tests/demo',
  timeout: 900000,
  retries: 0,
  use: {
    baseURL: 'http://localhost:5173',
    headless: true,
    viewport: { width: 1280, height: 800 },
    video: 'on',
    screenshot: 'on',
    launchOptions: {
      executablePath: '/usr/bin/google-chrome-stable',
    },
  },
  projects: [
    {
      name: 'chromium',
      use: { browserName: 'chromium' },
    },
  ],
})
