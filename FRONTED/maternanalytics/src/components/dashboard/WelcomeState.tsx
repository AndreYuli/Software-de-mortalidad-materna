import { useState } from 'react'

export interface WelcomeStateProps {
  onGoToUpload: (view: 'mortalidad' | 'morbilidad') => void
}

export function WelcomeState({ onGoToUpload }: WelcomeStateProps) {
  const [showChoices, setShowChoices] = useState(false)

  return (
    <div className="welcome-dashboard-shell">
      <div className="welcome-dashboard-card">
        <div className="welcome-icon-circle">📋</div>
        <h2 className="welcome-title">Análisis Epidemiológico</h2>
        <p className="welcome-microcopy">
          Aún no hay datos para analizar. Carga los registros de los Eventos 549 (Morbilidad) y 550 (Mortalidad) del
          SIVIGILA para generar el panel de control y los modelos de clustering.
        </p>

        {!showChoices ? (
          <button className="btn-welcome-cta" onClick={() => setShowChoices(true)}>
            Importar Datos Epidemiológicos
          </button>
        ) : (
          <div className="upload-choices-panel">
            <button className="btn-choice-upload" onClick={() => onGoToUpload('mortalidad')}>
              <span className="btn-choice-upload-icon">🩸</span>
              <span className="btn-choice-upload-label">Mortalidad</span>
              <span className="btn-choice-upload-sublabel">Evento 550</span>
            </button>
            <button className="btn-choice-upload" onClick={() => onGoToUpload('morbilidad')}>
              <span className="btn-choice-upload-icon">🏥</span>
              <span className="btn-choice-upload-label">Morbilidad Extrema</span>
              <span className="btn-choice-upload-sublabel">Evento 549</span>
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
