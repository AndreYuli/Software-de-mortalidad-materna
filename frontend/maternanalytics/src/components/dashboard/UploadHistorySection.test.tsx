import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { UploadHistorySection } from './UploadHistorySection'

const fetchHistorial = vi.hoisted(() => vi.fn())
const actualizarCarga = vi.hoisted(() => vi.fn())
const eliminarCarga = vi.hoisted(() => vi.fn())
vi.mock('../../api', () => ({ fetchHistorial, actualizarCarga, eliminarCarga }))

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
    actualizarCarga.mockReset().mockResolvedValue(undefined)
    eliminarCarga.mockReset().mockResolvedValue(undefined)
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

  it('edita una carga: envía nombre y fecha en hora local y recarga el historial', async () => {
    render(<UploadHistorySection />)
    fireEvent.click(await screen.findByRole('button', { name: 'Editar archivo_1.xlsx' }))

    const dialogo = screen.getByRole('dialog', { name: 'Editar carga' })
    expect(dialogo).toBeTruthy()
    // 15:00 UTC = 10:00 en Colombia
    expect((screen.getByLabelText('Fecha de la carga') as HTMLInputElement).value).toBe('2026-09-15T10:00')

    fireEvent.change(screen.getByLabelText('Nombre del archivo'), { target: { value: 'corregido.xlsx' } })
    fireEvent.click(screen.getByRole('button', { name: 'Guardar cambios' }))

    await waitFor(() =>
      expect(actualizarCarga).toHaveBeenCalledWith(1, { nombre_archivo: 'corregido.xlsx', fecha_carga: '2026-09-15T10:00' }),
    )
    await waitFor(() => expect(screen.queryByRole('dialog')).toBeNull())
    expect(fetchHistorial).toHaveBeenCalledTimes(2)
  })

  it('muestra el error del servidor al editar y mantiene el diálogo abierto', async () => {
    actualizarCarga.mockRejectedValue(new Error('El nombre del archivo no puede estar vacío.'))
    render(<UploadHistorySection />)
    fireEvent.click(await screen.findByRole('button', { name: 'Editar archivo_1.xlsx' }))
    fireEvent.click(screen.getByRole('button', { name: 'Guardar cambios' }))
    expect((await screen.findByRole('alert')).textContent).toContain('no puede estar vacío')
    expect(screen.getByRole('dialog', { name: 'Editar carga' })).toBeTruthy()
  })

  it('elimina una carga solo tras confirmar', async () => {
    render(<UploadHistorySection />)
    fireEvent.click(await screen.findByRole('button', { name: 'Eliminar archivo_1.xlsx' }))
    expect(eliminarCarga).not.toHaveBeenCalled()

    fireEvent.click(within(screen.getByRole('dialog', { name: 'Eliminar carga' })).getByRole('button', { name: 'Eliminar' }))
    await waitFor(() => expect(eliminarCarga).toHaveBeenCalledWith(1))
    await waitFor(() => expect(screen.queryByRole('dialog')).toBeNull())
    expect(fetchHistorial).toHaveBeenCalledTimes(2)
  })

  it('cancelar la eliminación no borra nada', async () => {
    render(<UploadHistorySection />)
    fireEvent.click(await screen.findByRole('button', { name: 'Eliminar archivo_1.xlsx' }))
    fireEvent.click(screen.getByRole('button', { name: 'Cancelar' }))
    expect(screen.queryByRole('dialog')).toBeNull()
    expect(eliminarCarga).not.toHaveBeenCalled()
  })
})
