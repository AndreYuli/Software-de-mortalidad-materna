import React, { useState, useRef, useEffect } from 'react'
import { Send, Bot, X, MessageSquare, Loader2 } from 'lucide-react'
import { enviarMensajeChat, type ChatMensaje } from '../../api'

interface ChatWidgetProps {
  analisisId: number
  filtros?: { year?: string; month?: string }
}

export const ChatWidget: React.FC<ChatWidgetProps> = ({ analisisId, filtros }) => {
  const [isOpen, setIsOpen] = useState(false)
  const [historial, setHistorial] = useState<ChatMensaje[]>([
    { rol: 'asistente', contenido: '¡Hola! Puedes hacerme preguntas sobre los datos de este análisis. ¿En qué te puedo ayudar?' }
  ])
  const [pregunta, setPregunta] = useState('')
  const [cargando, setCargando] = useState(false)
  const [error, setError] = useState<string | null>(null)
  
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (isOpen) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }
  }, [historial, isOpen])

  const handleEnviar = async (e?: React.FormEvent) => {
    e?.preventDefault()
    if (!pregunta.trim() || cargando) return

    const nuevoMensaje: ChatMensaje = { rol: 'usuario', contenido: pregunta.trim() }
    const nuevoHistorial = [...historial, nuevoMensaje]
    
    setHistorial(nuevoHistorial)
    setPregunta('')
    setCargando(true)
    setError(null)

    try {
      // Limitar el historial a los últimos 6 mensajes para no exceder el contexto del LLM
      const historialRecortado = nuevoHistorial.slice(-6)
      const respuesta = await enviarMensajeChat(analisisId, nuevoMensaje.contenido, historialRecortado.slice(0, -1), filtros)
      
      if (respuesta === null) {
        setError('El servicio de IA no está disponible en este momento.')
      } else {
        setHistorial(prev => [...prev, { rol: 'asistente', contenido: respuesta.respuesta }])
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ocurrió un error inesperado.')
    } finally {
      setCargando(false)
    }
  }

  return (
    <>
      {/* Botón flotante para abrir el chat */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="fixed bottom-6 right-6 p-4 bg-brand-magenta text-white rounded-full shadow-lg hover:bg-brand-violet transition-colors z-50 flex items-center justify-center"
        aria-label="Abrir asistente de IA"
      >
        {isOpen ? <X size={24} /> : <MessageSquare size={24} />}
      </button>

      {/* Ventana del chat */}
      {isOpen && (
        <div className="fixed bottom-24 right-6 w-80 sm:w-96 bg-white rounded-xl shadow-2xl border border-gray-200 flex flex-col z-50 overflow-hidden h-[500px] max-h-[calc(100dvh-120px)]">
          {/* Cabecera */}
          <div className="bg-brand-deep text-white p-4 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Bot size={20} />
              <h3 className="font-semibold">Asistente de Análisis</h3>
            </div>
            <button onClick={() => setIsOpen(false)} className="text-gray-300 hover:text-white">
              <X size={20} />
            </button>
          </div>

          {/* Área de mensajes */}
          <div className="flex-1 overflow-y-auto p-4 bg-slate-50 flex flex-col gap-3">
            {historial.map((msg, idx) => (
              <div key={idx} className={`flex ${msg.rol === 'usuario' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[85%] rounded-2xl p-3 text-sm shadow-sm ${msg.rol === 'usuario' ? 'bg-brand-magenta text-white rounded-tr-sm' : 'bg-white text-gray-800 border border-gray-200 rounded-tl-sm'}`}>
                  {msg.contenido}
                </div>
              </div>
            ))}
            
            {cargando && (
              <div className="flex justify-start">
                <div className="bg-white text-gray-800 border border-gray-200 rounded-2xl rounded-tl-sm p-3 text-sm shadow-sm flex items-center gap-2">
                  <Loader2 size={16} className="animate-spin text-brand-magenta" />
                  Escribiendo...
                </div>
              </div>
            )}
            
            {error && (
              <div className="text-center p-2 bg-red-50 text-red-600 text-xs rounded-lg border border-red-100">
                {error}
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>

          {/* Zona de input */}
          <div className="p-3 bg-white border-t border-gray-200">
            <form onSubmit={handleEnviar} className="flex items-center gap-2">
              <input
                type="text"
                value={pregunta}
                onChange={(e) => setPregunta(e.target.value)}
                placeholder="Pregunta sobre los datos..."
                className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-magenta focus:border-transparent text-sm"
                disabled={cargando}
              />
              <button
                type="submit"
                disabled={!pregunta.trim() || cargando}
                className="p-2 bg-brand-magenta text-white rounded-lg hover:bg-brand-violet disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center"
              >
                <Send size={18} />
              </button>
            </form>
          </div>
        </div>
      )}
    </>
  )
}
