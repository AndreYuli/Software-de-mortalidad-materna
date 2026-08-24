import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { AtencionOportunidad } from './AtencionOportunidad'

const kpis = {
  cpnPromedio: 4.2,
  gestacionesPromedio: 2.1,
  estanciaHospitalaria: 3.5,
  estanciaUci: 1.2,
  totalMort: 10,
  totalMorb: 40,
}

const institucionReferencia = {
  instituciones: ['Hospital A', 'Hospital B'],
  conteos: [10, 6],
  con_uci: [2, 1],
  con_cirugia: [1, 0],
  totalConDato: 16,
  totalCasos: 20,
}

const obstetricoEdad = [
  {
    label: 'Gestaciones',
    mort: { nombre: 'Gestaciones', valoresEje: [0, 1, 2], conteos: [1, 2, 3], porEdad: {}, promedio: 2, total: 6 },
    morb: null,
  },
]

describe('AtencionOportunidad', () => {
  it('renderiza KPIs, instituciones y variables obstétricas sin lanzar excepciones', () => {
    render(
      <AtencionOportunidad kpis={kpis} institucionReferencia={institucionReferencia} obstetricoEdad={obstetricoEdad} />,
    )
    expect(screen.getByText('Instituciones de Referencia (Morbilidad)')).toBeInTheDocument()
    expect(screen.getByText('Variables Obstétricas por Edad')).toBeInTheDocument()
    expect(screen.getByText('4 días')).toBeInTheDocument()
  })

  it('muestra el mensaje de datos insuficientes cuando no hay nada', () => {
    render(<AtencionOportunidad kpis={null} institucionReferencia={null} obstetricoEdad={null} />)
    expect(screen.getByText('No hay datos suficientes para generar este análisis.')).toBeInTheDocument()
  })
})
