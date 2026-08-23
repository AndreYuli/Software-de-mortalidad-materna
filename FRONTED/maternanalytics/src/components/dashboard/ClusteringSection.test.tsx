import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ClusteringSection } from './ClusteringSection'
import type { ClusteringChartData } from '../../hooks/dashboard/useDashboardCharts'

const chartData2d: ClusteringChartData = {
  dim: '2d',
  points: [
    { x: 1, y: 2, color: '#0066cc', label: 'Caso 1 · Cluster 0' },
    { x: -1, y: 0.5, color: '#c0392b', label: 'Caso 2 · Cluster 1' },
  ],
}

const chartData3d: ClusteringChartData = {
  dim: '3d',
  points: [{ x: 1, y: 2, z: 0.5, color: '#0066cc', label: 'Caso 1 · Cluster 0' }],
}

const baseProps = {
  segmento: 'mortalidad' as const,
  clusteringSegment: 'mortalidad' as const,
  onClusteringSegmentChange: () => {},
  onPcaDimChange: () => {},
  activeClusterData: { clusters: [0, 1], pca_2d: { x: [1, -1], y: [2, 0.5] } },
  latestMortalidad: { id: 1 },
  latestMorbilidad: null,
  filterYear: '',
  filterMonth: '',
}

describe('ClusteringSection', () => {
  it('renderiza el scatter 2D sin lanzar excepciones cuando hay datos', () => {
    render(<ClusteringSection {...baseProps} pcaDim="2d" clusteringChartData={chartData2d} />)
    expect(screen.getByText('Modelos de Clustering (PCA)')).toBeInTheDocument()
  })

  it('renderiza el scatter 3D sin lanzar excepciones cuando hay datos', () => {
    render(<ClusteringSection {...baseProps} pcaDim="3d" clusteringChartData={chartData3d} />)
    expect(screen.getByText('Modelos de Clustering (PCA)')).toBeInTheDocument()
  })

  it('muestra el mensaje de modelo no disponible cuando no hay datos', () => {
    render(<ClusteringSection {...baseProps} activeClusterData={null} pcaDim="2d" clusteringChartData={null} />)
    expect(screen.getByText(/Modelo de clustering no disponible/)).toBeInTheDocument()
  })
})
