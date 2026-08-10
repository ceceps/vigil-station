import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import Shimmer from '../components/Shimmer'

describe('Shimmer Component', () => {
  describe('table type', () => {
    it('renders table shimmer with default rows', () => {
      render(<Shimmer type="table" />)
      const rows = document.querySelectorAll('.shimmer-row')
      expect(rows.length).toBe(5)
    })

    it('renders table shimmer with custom rows', () => {
      render(<Shimmer type="table" rows={3} />)
      const rows = document.querySelectorAll('.shimmer-row')
      expect(rows.length).toBe(3)
    })

    it('renders shimmer header', () => {
      render(<Shimmer type="table" />)
      const header = document.querySelector('.shimmer-header')
      expect(header).toBeTruthy()
    })
  })

  describe('card type', () => {
    it('renders card shimmer with default rows', () => {
      render(<Shimmer type="card" />)
      const cards = document.querySelectorAll('.shimmer-card')
      expect(cards.length).toBe(5)
    })

    it('renders card shimmer with custom rows', () => {
      render(<Shimmer type="card" rows={2} />)
      const cards = document.querySelectorAll('.shimmer-card')
      expect(cards.length).toBe(2)
    })

    it('renders card header and content', () => {
      render(<Shimmer type="card" rows={1} />)
      const header = document.querySelector('.shimmer-card-header')
      const content = document.querySelector('.shimmer-card-content')
      expect(header).toBeTruthy()
      expect(content).toBeTruthy()
    })
  })

  describe('stats type', () => {
    it('renders stats shimmer with 3 stat cards', () => {
      render(<Shimmer type="stats" />)
      const statCards = document.querySelectorAll('.shimmer-stat-card')
      expect(statCards.length).toBe(3)
    })

    it('renders stat value and label', () => {
      render(<Shimmer type="stats" />)
      const values = document.querySelectorAll('.shimmer-stat-value')
      const labels = document.querySelectorAll('.shimmer-stat-label')
      expect(values.length).toBe(3)
      expect(labels.length).toBe(3)
    })
  })

  describe('default type', () => {
    it('returns null for unknown type', () => {
      const { container } = render(<Shimmer type="unknown" />)
      expect(container.innerHTML).toBe('')
    })
  })
})
