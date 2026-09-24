import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { ChatWidget } from './ChatWidget'
import * as api from '../../api'

// Mock de la API
vi.mock('../../api', async () => {
  const actual = await vi.importActual('../../api')
  return {
    ...actual,
    enviarMensajeChat: vi.fn()
  }
})

describe('ChatWidget', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    
    // Polyfill para scrollIntoView
    window.HTMLElement.prototype.scrollIntoView = vi.fn()
  })

  it('renderiza el botón flotante inicialmente', () => {
    render(<ChatWidget analisisId={1} />)
    const toggleBtn = screen.getByRole('button', { name: /abrir asistente/i })
    expect(toggleBtn).toBeInTheDocument()
  })

  it('abre el chat al hacer clic en el botón', () => {
    render(<ChatWidget analisisId={1} />)
    const toggleBtn = screen.getByRole('button', { name: /abrir asistente/i })
    fireEvent.click(toggleBtn)
    
    expect(screen.getByText('Asistente de Análisis')).toBeInTheDocument()
    expect(screen.getByText('¡Hola! Puedes hacerme preguntas sobre los datos de este análisis. ¿En qué te puedo ayudar?')).toBeInTheDocument()
  })

  it('envía un mensaje y muestra la respuesta', async () => {
    vi.mocked(api.enviarMensajeChat).mockResolvedValueOnce({ respuesta: 'Respuesta del bot', modelo: 'qwen' })
    
    render(<ChatWidget analisisId={1} />)
    fireEvent.click(screen.getByRole('button', { name: /abrir asistente/i }))
    
    const input = screen.getByPlaceholderText(/pregunta sobre los datos/i)
    fireEvent.change(input, { target: { value: 'Una pregunta' } })
    fireEvent.submit(input.closest('form')!)
    
    // Aparece mensaje del usuario
    expect(screen.getByText('Una pregunta')).toBeInTheDocument()
    
    // Mientras carga
    expect(screen.getByText('Escribiendo...')).toBeInTheDocument()
    
    // Resuelve
    await waitFor(() => {
      expect(screen.queryByText('Escribiendo...')).not.toBeInTheDocument()
    })
    
    expect(screen.getByText('Respuesta del bot')).toBeInTheDocument()
    expect(api.enviarMensajeChat).toHaveBeenCalledWith(1, 'Una pregunta', [
      { rol: 'asistente', contenido: '¡Hola! Puedes hacerme preguntas sobre los datos de este análisis. ¿En qué te puedo ayudar?' }
    ], undefined)
  })

  it('muestra mensaje de error si el servicio devuelve null', async () => {
    vi.mocked(api.enviarMensajeChat).mockResolvedValueOnce(null)
    
    render(<ChatWidget analisisId={1} />)
    fireEvent.click(screen.getByRole('button', { name: /abrir asistente/i }))
    
    const input = screen.getByPlaceholderText(/pregunta sobre los datos/i)
    fireEvent.change(input, { target: { value: 'Una pregunta' } })
    fireEvent.submit(input.closest('form')!)
    
    await waitFor(() => {
      expect(screen.getByText('El servicio de IA no está disponible en este momento.')).toBeInTheDocument()
    })
  })

  it('muestra mensaje de error si la API falla', async () => {
    vi.mocked(api.enviarMensajeChat).mockRejectedValueOnce(new Error('Fallo de red'))
    
    render(<ChatWidget analisisId={1} />)
    fireEvent.click(screen.getByRole('button', { name: /abrir asistente/i }))
    
    const input = screen.getByPlaceholderText(/pregunta sobre los datos/i)
    fireEvent.change(input, { target: { value: 'Una pregunta' } })
    fireEvent.submit(input.closest('form')!)
    
    await waitFor(() => {
      expect(screen.getByText('Fallo de red')).toBeInTheDocument()
    })
  })
})
