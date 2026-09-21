import { beforeEach, describe, expect, it, vi } from 'vitest'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { CruceVariablesSection } from './CruceVariablesSection'

interface BarOptions {
  plugins: { title: { text: string }; legend: { title: { text: string } } }
  scales: { x: { title: { text: string } }; y: { title: { text: string } } }
}

const fetchCruce = vi.hoisted(() => vi.fn())
const barProps = vi.hoisted(() => ({ last: null as null | { options: unknown } }))

vi.mock('../../api', () => ({ fetchCruce }))
vi.mock('react-chartjs-2', () => ({
  Bar: (props: { options: unknown }) => {
    barProps.last = props
    return <canvas data-testid="bar" />
  },
}))

const respuesta = {
  categorias_socio: ['Urbana', 'Rural'],
  categorias_clinica: ['0', '1'],
  matriz: [
    [3, 1],
    [2, 4],
  ],
  total: 10,
  var_socio_label: 'x',
  var_clinica_label: 'y',
}

describe('CruceVariablesSection: etiquetas dinámicas (DEC-002)', () => {
  beforeEach(() => {
    fetchCruce.mockReset()
    fetchCruce.mockResolvedValue(respuesta)
  })

  it('nombra las variables seleccionadas en título, ejes y leyenda, y las actualiza al cambiarlas', async () => {
    render(<CruceVariablesSection analisisId={1} evento="Morbilidad" />)
    await screen.findByTestId('bar')

    const opciones = () => barProps.last!.options as BarOptions
    let o = opciones()
    expect(o.plugins.title.text).toBe('Zona de residencia según N° de gestaciones')
    expect(o.scales.x.title.text).toBe('Casos — Zona de residencia')
    expect(o.scales.y.title.text).toBe('Zona de residencia')
    expect(o.plugins.legend.title.text).toBe('N° de gestaciones')

    fireEvent.change(screen.getByLabelText('Variable sociodemográfica'), { target: { value: 'etnia' } })
    fireEvent.change(screen.getByLabelText('Variable clínica'), { target: { value: 'cesareas' } })

    await waitFor(() => expect(fetchCruce).toHaveBeenLastCalledWith(1, 'etnia', 'cesareas'))
    await waitFor(() => expect(opciones().plugins.title.text).toBe('Etnia según Cesáreas'))
    o = opciones()
    expect(o.scales.x.title.text).toBe('Casos — Etnia')
    expect(o.scales.y.title.text).toBe('Etnia')
    expect(o.plugins.legend.title.text).toBe('Cesáreas')
  })
})
