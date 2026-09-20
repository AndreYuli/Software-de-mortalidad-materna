import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { UploadHistorySection } from './UploadHistorySection'

const fetchHistorial = vi.hoisted(() => vi.fn())
vi.mock('../../api', () => ({ fetchHistorial }))

const item = (id: number, over: Record<string, unknown> = {}) => ({
  id,
  tipo: 'mortalidad',
  nombre_archivo: `archivo_${id}.xlsx`,
  archivo: '/media/x.xlsx',
  fecha_carga: '2026-09-15T15:00:00',
  anio: 2026,
  mes: 9,
  semana: 38,
  total_registros: 10,
  resumen: {},
  ...over,
})

const respuesta = (items: unknown[], over: Record<string, unknown> = {}) => ({
  items,
  total: items.length,
  page: 1,
  per_page: 20,
  total_pages: items.length ? 1 : 0,
  anios_disponibles: [2026, 2025],
  ...over,
})

describe('UploadHistorySection', () => {
  beforeEach(() => {
    fetchHistorial.mockReset()
    fetchHistorial.mockResolvedValue(respuesta([item(1)]))
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('muestra las columnas Año, Mes y Semana de cada carga', async () => {
    fetchHistorial.mockResolvedValue(respuesta([item(1, { anio: 2026, mes: 9, semana: 38 })]))
    render(<UploadHistorySection />)

    for (const columna of ['Año', 'Mes', 'Semana']) {
      expect(await screen.findByRole('columnheader', { name: columna })).toBeTruthy()
    }
    const fila = screen.getByText('archivo_1.xlsx').closest('tr')!
    expect(fila.textContent).toContain('2026')
    expect(fila.textContent).toContain('Septiembre')
    expect(fila.textContent).toContain('38')
  })

  it('carga sin filtros la primera vez y ofrece los años disponibles', async () => {
    render(<UploadHistorySection />)
    await screen.findByText('archivo_1.xlsx')
    expect(fetchHistorial).toHaveBeenCalledWith(1, 20, { q: '', tipo: '', year: '', month: '', week: '' }, expect.anything())
    const anios = screen.getByLabelText('Año') as HTMLSelectElement
    expect([...anios.options].map((o) => o.value)).toEqual(['', '2026', '2025'])
  })

  it('los selectores filtran en el servidor y vuelven a la primera página', async () => {
    render(<UploadHistorySection />)
    await screen.findByText('archivo_1.xlsx')

    fireEvent.change(screen.getByLabelText('Evento'), { target: { value: 'morbilidad' } })
    fireEvent.change(screen.getByLabelText('Año'), { target: { value: '2025' } })
    fireEvent.change(screen.getByLabelText('Mes'), { target: { value: '8' } })
    fireEvent.change(screen.getByLabelText('Semana'), { target: { value: '34' } })

    await waitFor(() =>
      expect(fetchHistorial).toHaveBeenLastCalledWith(
        1,
        20,
        { q: '', tipo: 'morbilidad', year: '2025', month: '8', week: '34' },
        expect.anything(),
      ),
    )
  })

  it('la búsqueda espera a que se deje de escribir y el campo no se desmonta al consultar', async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true })
    render(<UploadHistorySection />)
    await screen.findByText('archivo_1.xlsx')
    fetchHistorial.mockClear()

    const campo = screen.getByLabelText('Buscar') as HTMLInputElement
    fireEvent.change(campo, { target: { value: 'sem' } })
    fireEvent.change(campo, { target: { value: 'semana37' } })
    expect(fetchHistorial).not.toHaveBeenCalled() // aún dentro del retraso

    await act(async () => {
      vi.advanceTimersByTime(350)
    })
    await waitFor(() => expect(fetchHistorial).toHaveBeenCalledTimes(1))
    expect(fetchHistorial).toHaveBeenCalledWith(1, 20, expect.objectContaining({ q: 'semana37' }), expect.anything())

    // Sigue siendo el mismo elemento (con su foco y su texto) mientras se consulta
    expect(screen.getByLabelText('Buscar')).toBe(campo)
    expect(campo.value).toBe('semana37')
  })

  it('sin resultados con filtros muestra el estado vacío y permite limpiarlos', async () => {
    render(<UploadHistorySection />)
    await screen.findByText('archivo_1.xlsx')

    fetchHistorial.mockResolvedValue(respuesta([]))
    fireEvent.change(screen.getByLabelText('Evento'), { target: { value: 'morbilidad' } })
    expect(await screen.findByText('Ninguna carga coincide con la búsqueda o los filtros.')).toBeTruthy()
    expect(screen.getByText('0 cargas que coinciden con los filtros')).toBeTruthy()

    fetchHistorial.mockResolvedValue(respuesta([item(1)]))
    fireEvent.click(screen.getByText('Limpiar filtros'))
    expect(await screen.findByText('archivo_1.xlsx')).toBeTruthy()
    expect((screen.getByLabelText('Evento') as HTMLSelectElement).value).toBe('')
    expect(screen.queryByText('Limpiar filtros')).toBeNull()
  })

  it('sin cargas y sin filtros invita a subir un archivo', async () => {
    fetchHistorial.mockResolvedValue(respuesta([]))
    render(<UploadHistorySection />)
    expect(await screen.findByText(/No hay cargas registradas aún/)).toBeTruthy()
  })

  it('ante un error conserva los filtros y permite reintentar', async () => {
    fetchHistorial.mockRejectedValueOnce(new Error('Error al obtener historial: 500'))
    render(<UploadHistorySection />)
    expect(await screen.findByRole('alert')).toBeTruthy()
    expect(screen.getByLabelText('Buscar')).toBeTruthy()

    fireEvent.click(screen.getByText('Reintentar'))
    expect(await screen.findByText('archivo_1.xlsx')).toBeTruthy()
  })
})
