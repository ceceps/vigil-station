import React from 'react'

function Shimmer({ type = 'table', rows = 5 }) {
  if (type === 'table') {
    return (
      <div className="shimmer-table">
        <div className="shimmer-header">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="shimmer-cell shimmer-animate"></div>
          ))}
        </div>
        {[...Array(rows)].map((_, rowIndex) => (
          <div key={rowIndex} className="shimmer-row">
            {[...Array(6)].map((_, cellIndex) => (
              <div key={cellIndex} className="shimmer-cell shimmer-animate"></div>
            ))}
          </div>
        ))}
      </div>
    )
  }

  if (type === 'card') {
    return (
      <div className="shimmer-cards">
        {[...Array(rows)].map((_, i) => (
          <div key={i} className="shimmer-card">
            <div className="shimmer-card-header shimmer-animate"></div>
            <div className="shimmer-card-content">
              <div className="shimmer-line shimmer-animate"></div>
              <div className="shimmer-line shimmer-animate"></div>
              <div className="shimmer-line short shimmer-animate"></div>
            </div>
          </div>
        ))}
      </div>
    )
  }

  if (type === 'stats') {
    return (
      <div className="shimmer-stats">
        {[...Array(3)].map((_, i) => (
          <div key={i} className="shimmer-stat-card">
            <div className="shimmer-stat-value shimmer-animate"></div>
            <div className="shimmer-stat-label shimmer-animate"></div>
          </div>
        ))}
      </div>
    )
  }

  return null
}

export default Shimmer
