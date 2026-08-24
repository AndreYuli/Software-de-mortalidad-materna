import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { SeveridadFallasMorbilidad } from './SeveridadFallasMorbilidad'

const data = {
  fallas: [{ nombre: 'Falla Cardiaca', casos: 4 }, { nombre: 'Falla Renal', casos: 2 }, { nombre: 'Falla Hepática', casos: 1 }],
  severidad: [{ nombre: 'Ingreso UCI', casos: 5 }],
  total_casos: 10,
}

const morbKpis = { totalCasos: 10, edadPromedio: 28.5, estanciaHospitalaria: 4.2, estanciaUci: 1.1, criteriosPromedio: 2.3 }
const criteriosInclusion = [{ nombre: 'Hemorragia', casos: 6, porcentaje: 60 }]
const momentoOcurrencia = [{ label: 'Parto', count: 5 }, { label: 'Puerperio', count: 5 }]
const tiempoRemision = { valores: [1, 2, 3, 4, 5], min: 1, q1: 2, median: 3, mean: 3, q3: 4, max: 5, total: 5 }

describe('SeveridadFallasMorbilidad', () => {
  it('renderiza las secciones con gráficos sin lanzar excepciones cuando hay datos', () => {
    render(
      <SeveridadFallasMorbilidad
        data={data}
        morbKpis={morbKpis}
        criteriosInclusion={criteriosInclusion}
        momentoOcurrencia={momentoOcurrencia}
        tiempoRemision={tiempoRemision}
      />,
    )
    expect(screen.getByText('Criterios de Inclusión MME')).toBeInTheDocument()
    expect(screen.getByText('Momento de Ocurrencia')).toBeInTheDocument()
    expect(screen.getByText('Tiempo de Remisión')).toBeInTheDocument()
  })

  it('muestra el mensaje de datos insuficientes cuando no hay nada', () => {
    render(
      <SeveridadFallasMorbilidad
        data={undefined}
        morbKpis={null}
        criteriosInclusion={null}
        momentoOcurrencia={null}
        tiempoRemision={null}
      />,
    )
    expect(screen.getByText(/No hay datos suficientes de morbilidad/)).toBeInTheDocument()
  })
})
