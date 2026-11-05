import { beforeEach, describe, expect, it, vi } from 'vitest'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { NarrativasResumen } from './NarrativasResumen'

const obtenerNarrativa = vi.hoisted(() => vi.fn())
vi.mock('../../api', () => ({ obtenerNarrativa }))

const base = {
  latestMortalidad: { id: 10 },
  latestMorbilidad: { id: 20 },
  filterYear: '2026',
  filterMonth: '',
}

describe('NarrativasResumen', () => {
  beforeEach(() => {
    obtenerNarrativa.mockReset()
  })

  it('con ambos eventos muestra un resumen por evento, sin generar nada hasta que se pide', () => {
    render(<NarrativasResumen {...base} segmento="ambos" />)
    expect(screen.getByText(/Resumen ejecutivo · Mortalidad/)).toBeTruthy()
    expect(screen.getByText(/Resumen ejecutivo · Morbilidad/)).toBeTruthy()
    expect(obtenerNarrativa).not.toHaveBeenCalled()
  })

  it('solo muestra el evento del segmento activo', () => {
    const { rerender } = render(<NarrativasResumen {...base} segmento="mortalidad" />)
    expect(screen.queryByText(/Morbilidad/)).toBeNull()
    expect(screen.getByText(/Mortalidad/)).toBeTruthy()

    rerender(<NarrativasResumen {...base} segmento="morbilidad" />)
    expect(screen.queryByText(/Mortalidad/)).toBeNull()
    expect(screen.getByText(/Morbilidad/)).toBeTruthy()
  })

  it('no renderiza nada si no hay análisis cargados', () => {
    const { container } = render(
      <NarrativasResumen {...base} latestMortalidad={null} latestMorbilidad={null} segmento="ambos" />,
    )
    expect(container.innerHTML).toBe('')
  })

  it('genera la narrativa con el análisis, el tipo y el periodo, y permite regenerar', async () => {
    obtenerNarrativa.mockResolvedValue({ narrativa: 'Texto generado', modelo: 'm', generado_en: 'x', desde_cache: false })
    render(<NarrativasResumen {...base} segmento="mortalidad" />)

    fireEvent.click(screen.getByText('Generar resumen IA'))
    expect(await screen.findByText('Texto generado')).toBeTruthy()
    expect(obtenerNarrativa).toHaveBeenCalledWith(10, 'resumen_ejecutivo', { year: '2026', month: '' }, false)

    fireEvent.click(screen.getByText('Regenerar'))
    await waitFor(() =>
      expect(obtenerNarrativa).toHaveBeenLastCalledWith(10, 'resumen_ejecutivo', { year: '2026', month: '' }, true),
    )
  })

  it('si el servicio de IA no está disponible (503) avisa y permite reintentar (no desaparece)', async () => {
    obtenerNarrativa.mockResolvedValueOnce(null)
    render(<NarrativasResumen {...base} segmento="mortalidad" />)
    fireEvent.click(screen.getByText('Generar resumen IA'))
    expect(await screen.findByText(/servicio de IA no está disponible/i)).toBeTruthy()

    obtenerNarrativa.mockResolvedValueOnce({ narrativa: 'Ya responde', modelo: 'm', generado_en: 'x', desde_cache: false })
    fireEvent.click(screen.getByText('Reintentar'))
    expect(await screen.findByText('Ya responde')).toBeTruthy()
  })

  it('muestra la verificación automática: cifras respaldadas, alertas y que no es validación clínica', async () => {
    obtenerNarrativa.mockResolvedValue({
      narrativa: 'Texto con cifras',
      modelo: 'm',
      generado_en: 'x',
      desde_cache: false,
      verificacion: {
        cifras_total: 4,
        cifras_respaldadas: 3,
        cifras_sin_respaldo: ['99'],
        alertas_coherencia: ['Lenguaje causal: un análisis descriptivo no permite afirmar relaciones de causa.'],
      },
    })
    render(<NarrativasResumen {...base} segmento="mortalidad" />)
    fireEvent.click(screen.getByText('Generar resumen IA'))
    expect(await screen.findByText(/3 de 4 cifras coinciden con los indicadores/)).toBeTruthy()
    expect(screen.getByText(/No respaldadas: 99/)).toBeTruthy()
    expect(screen.getByText(/Lenguaje causal/)).toBeTruthy()
    expect(screen.getByText(/no es una validación clínica/i)).toBeTruthy()
  })

  it('ante un error de red muestra un mensaje y permite reintentar (no se queda cargando)', async () => {
    vi.spyOn(console, 'error').mockImplementation(() => {})
    obtenerNarrativa.mockRejectedValueOnce(new Error('Failed to fetch'))
    render(<NarrativasResumen {...base} segmento="mortalidad" />)
    fireEvent.click(screen.getByText('Generar resumen IA'))
    expect(await screen.findByRole('alert')).toBeTruthy()

    obtenerNarrativa.mockResolvedValueOnce({ narrativa: 'Ahora sí', modelo: 'm', generado_en: 'x', desde_cache: true })
    fireEvent.click(screen.getByText('Reintentar'))
    expect(await screen.findByText('Ahora sí')).toBeTruthy()
  })
})
