import React from 'react'

export interface ChartAiInsightProps {
  insight: string | null | undefined
}

export const ChartAiInsight: React.FC<ChartAiInsightProps> = ({ insight }) => {
  if (!insight) return null

  return (
    <div className="chart-ai-insight">
      <span>Lectura automatizada</span>
      <p>{insight}</p>
    </div>
  )
}
