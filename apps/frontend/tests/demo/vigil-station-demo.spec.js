import { test, expect } from '@playwright/test'

test.describe('Vigil Station Demo Recording', () => {
  test('full walkthrough - all tabs', async ({ page }) => {
    await page.goto('/')
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(5000)
    await page.screenshot({ path: 'tests/demo/screenshots/01-dashboard.png' })

    // ===== SCHEDULE TAB =====
    await page.locator('button', { hasText: 'Schedule' }).click()
    // Wait for passes to load (table rows with data)
    await page.waitForFunction(() => {
      const rows = document.querySelectorAll('table tbody tr')
      return rows.length > 0
    }, { timeout: 30000 }).catch(() => {})
    await page.waitForTimeout(2000)

    // Select first satellite
    const satSelect = page.locator('select').first()
    await satSelect.waitFor({ state: 'visible', timeout: 10000 })
    const satOptions = await satSelect.locator('option').all()
    if (satOptions.length > 1) {
      const secondSatValue = await satOptions[1].getAttribute('value')
      if (secondSatValue) {
        await satSelect.selectOption(secondSatValue)
        await page.waitForTimeout(3000)
      }
    }

    // Select first ground station
    const gsSelect = page.locator('select').nth(1)
    await gsSelect.waitFor({ state: 'visible', timeout: 10000 })
    const gsOptions = await gsSelect.locator('option').all()
    if (gsOptions.length > 1) {
      const secondGsValue = await gsOptions[1].getAttribute('value')
      if (secondGsValue) {
        await gsSelect.selectOption(secondGsValue)
        await page.waitForTimeout(3000)
      }
    }

    await page.screenshot({ path: 'tests/demo/screenshots/02-schedule-filtered.png' })

    // Reset filters
    await satSelect.selectOption('')
    await gsSelect.selectOption('')
    await page.waitForTimeout(2000)
    await page.screenshot({ path: 'tests/demo/screenshots/02-schedule.png' })

    // Extra delay for voiceover to finish describing elevation color coding (green/yellow/red)
    await page.waitForTimeout(5000)

    // ===== CONFLICTS TAB =====
    await page.locator('button', { hasText: 'Conflicts' }).click()
    // Wait for conflict cards to load
    await page.waitForFunction(() => {
      const cards = document.querySelectorAll('.conflict-card')
      const noConflicts = document.querySelector('.no-conflicts')
      return cards.length > 0 || noConflicts
    }, { timeout: 30000 }).catch(() => {})
    await page.waitForTimeout(2000)
    await page.screenshot({ path: 'tests/demo/screenshots/03-conflicts.png' })

    // Wait for Generate AI Recommendation button to be visible and clickable
    const aiRecBtn = page.locator('button', { hasText: 'Generate AI Recommendation' }).first()
    if (await aiRecBtn.isVisible({ timeout: 5000 }).catch(() => false)) {
      await aiRecBtn.click()
      // Wait for recommendation to appear (suggested action text)
      await page.waitForFunction(() => {
        const rec = document.querySelector('.recommendation')
        return rec && rec.textContent.includes('Suggested Action')
      }, { timeout: 60000 }).catch(() => {})
      await page.waitForTimeout(2000)
      await page.screenshot({ path: 'tests/demo/screenshots/03b-conflicts-ai-recommendation.png' })
    }

    // Extra delay for voiceover to finish describing conflicts and AI recommendation
    await page.waitForTimeout(5000)

    // ===== APPROVALS TAB =====
    await page.locator('button', { hasText: 'Approvals' }).click()
    // Wait for approvals to load
    await page.waitForFunction(() => {
      const cards = document.querySelectorAll('.approval-card')
      const noApprovals = document.querySelector('.no-conflicts')
      return cards.length > 0 || noApprovals
    }, { timeout: 30000 }).catch(() => {})
    await page.waitForTimeout(2000)
    await page.screenshot({ path: 'tests/demo/screenshots/04-approvals.png' })

    // Click Generate Recommendation if no recommendation yet
    const genRecBtn = page.locator('button', { hasText: 'Generate Recommendation' }).first()
    if (await genRecBtn.isVisible({ timeout: 5000 }).catch(() => false)) {
      await genRecBtn.click()
      // Wait for recommendation to appear
      await page.waitForFunction(() => {
        const rec = document.querySelector('.recommendation-summary')
        return rec && rec.textContent.includes('Action')
      }, { timeout: 30000 }).catch(() => {})
      await page.waitForTimeout(2000)
      await page.screenshot({ path: 'tests/demo/screenshots/04b-approvals-with-rec.png' })
    }

    // Approve if visible
    const approveBtn = page.locator('button', { hasText: 'Approve Recommendation' }).first()
    if (await approveBtn.isVisible({ timeout: 5000 }).catch(() => false)) {
      await approveBtn.click()
      // Wait for approved status badge
      await page.waitForFunction(() => {
        const badge = document.querySelector('.status-badge.approved')
        const result = document.querySelector('.approval-result')
        return badge || result
      }, { timeout: 15000 }).catch(() => {})
      await page.waitForTimeout(2000)
      await page.screenshot({ path: 'tests/demo/screenshots/04c-approvals-approved.png' })
    }

    // Override if visible
    page.on('dialog', async (dialog) => {
      await dialog.accept('Operator override: alternative window preferred for ground station maintenance')
    })
    const overrideBtn = page.locator('button', { hasText: 'Override' }).first()
    if (await overrideBtn.isVisible({ timeout: 5000 }).catch(() => false)) {
      await overrideBtn.click()
      // Wait for overridden status badge
      await page.waitForFunction(() => {
        const badge = document.querySelector('.status-badge.overridden')
        const result = document.querySelector('.approval-result')
        return badge || result
      }, { timeout: 15000 }).catch(() => {})
      await page.waitForTimeout(2000)
      await page.screenshot({ path: 'tests/demo/screenshots/04d-approvals-overridden.png' })
    }

    // Extra delay for voiceover to finish describing approvals and audit logging
    await page.waitForTimeout(5000)

    // ===== MAP TAB =====
    await page.locator('button', { hasText: 'Map' }).click()
    await page.waitForSelector('.leaflet-map-container', { timeout: 15000 })
    await page.waitForTimeout(3000)
    // Zoom out multiple times to show all satellite blue dots
    const zoomOutBtn = page.locator('.leaflet-control-zoom-out')
    for (let i = 0; i < 4; i++) {
      if (await zoomOutBtn.isVisible()) {
        await zoomOutBtn.click()
        await page.waitForTimeout(500)
      }
    }
    await page.waitForTimeout(5000)
    await page.screenshot({ path: 'tests/demo/screenshots/05-map.png' })

    // ===== SPACE WEATHER TAB =====
    await page.locator('button', { hasText: 'Space Weather' }).click()
    // Wait for space weather data to load
    await page.waitForFunction(() => {
      const stats = document.querySelectorAll('.stat-value')
      return stats.length > 0 && stats[0].textContent.trim().length > 0
    }, { timeout: 30000 }).catch(() => {})
    await page.waitForTimeout(5000)
    await page.screenshot({ path: 'tests/demo/screenshots/06-space-weather.png' })

    // ===== ANALYTICS TAB =====
    await page.locator('button', { hasText: 'Analytics' }).click()
    // Wait for analytics data to load
    await page.waitForFunction(() => {
      const stats = document.querySelectorAll('.stat-value')
      return stats.length > 0 && stats[0].textContent.trim().length > 0
    }, { timeout: 30000 }).catch(() => {})
    await page.waitForTimeout(5000)
    await page.screenshot({ path: 'tests/demo/screenshots/07-analytics.png' })

    await page.screenshot({ path: 'tests/demo/screenshots/08-final.png' })
  })
})
