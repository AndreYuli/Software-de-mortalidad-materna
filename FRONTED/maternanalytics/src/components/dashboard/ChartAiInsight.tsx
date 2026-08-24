import React from 'react'

export interface ChartAiInsightProps {
  insight: string | null | undefined
}

export const ChartAiInsight: React.FC<ChartAiInsightProps> = ({ insight }) => {
  if (!insight) return null

  return (
    <div
      style={{
        marginTop: '14px',
        padding: '12px 16px',
        borderRadius: '12px',
        background: 'linear-gradient(135deg, #f8fafc 0%, #faf5ff 100%)',
        border: '1px solid #e9d5ff',
        boxShadow: '0 1px 3px rgba(0, 0, 0, 0.02)',
        display: 'flex',
        flexDirection: 'column',
        gap: '6px',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <span
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '4px',
            background: 'linear-gradient(135deg, #7c3aed 0%, #6366f1 100%)',
            color: '#ffffff',
            padding: '2px 8px',
            borderRadius: '9999px',
            fontSize: '10.5px',
            fontWeight: 700,
            textTransform: 'uppercase',
            letterSpacing: '0.04em',
          }}
        >
          ✨ Resumen IA
        </span>
      </div>
      <p
        style={{
          margin: 0,
          fontSize: '12.5px',
          lineHeight: '1.5',
          color: '#334155',
          fontWeight: 500,
        }}
      >
        {insight}
      </p>
    </div>
  )
}
