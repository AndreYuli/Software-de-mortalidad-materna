import React, { useEffect, useState } from 'react'
import {
  exportReportToExcel,
  exportToCsv,
  printExecutiveMedicalReport,
  ReportExportData,
} from '../../utils/reportExporter'

export interface ExportReportModalProps {
  isOpen: boolean
  onClose: () => void
  reportData: ReportExportData
}

export const ExportReportModal: React.FC<ExportReportModalProps> = ({ isOpen, onClose, reportData }) => {
  const [selectedFormat, setSelectedFormat] = useState<'excel' | 'pdf' | 'csv'>('excel')
  const [isExporting, setIsExporting] = useState(false)
  const [exportError, setExportError] = useState<string | null>(null)

  useEffect(() => {
    if (!isOpen) return
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', onKeyDown)
    return () => document.removeEventListener('keydown', onKeyDown)
  }, [isOpen, onClose])

  if (!isOpen) return null

  const handleExport = () => {
    setIsExporting(true)
    setExportError(null)
    try {
      if (selectedFormat === 'excel') {
        exportReportToExcel(reportData)
      } else if (selectedFormat === 'pdf') {
        printExecutiveMedicalReport(reportData)
      } else if (selectedFormat === 'csv') {
        const headers = ['Diagnóstico CIE-10', 'Casos']
        const rows = reportData.causasPrincipales.causas.map((c, i) => [
          c,
          reportData.causasPrincipales.valores[i] || 0,
        ])
        exportToCsv(`Causas_CIE10_${reportData.periodo.anio || 'Consolidado'}`, headers, rows)
      }
      setTimeout(() => {
        setIsExporting(false)
        onClose()
      }, 400)
    } catch (err) {
      console.error('Error al exportar reporte:', err)
      setExportError('No se pudo generar el reporte. Intenta de nuevo o elige otro formato.')
      setIsExporting(false)
    }
  }

  return (
    <div

      onClick={onClose}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-label="Exportar reporte epidemiológico"

        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div>
          <div>
            <h2>
              Exportar Reporte Epidemiológico
            </h2>
            <p>
              Selecciona el formato de exportación para los datos consolidados.
            </p>
          </div>
          <button
            onClick={onClose}
            type="button"
            aria-label="Cerrar"

          >
            ✕
          </button>
        </div>

        {/* Info resumen */}
        <div

        >
          <div>
            <span>Periodo: </span>
            <b>{reportData.periodo.anio || 'Histórico'} {reportData.periodo.mes ? `(Mes ${reportData.periodo.mes})` : ''}</b>
          </div>
          <div>
            <span>Segmento: </span>
            <b>{reportData.periodo.segmento.toUpperCase()}</b>
          </div>
          <div>
            <span>Total Casos: </span>
            <b>{reportData.kpis.casosTotales}</b>
          </div>
          <div>
            <span>Letalidad: </span>
            <b>{reportData.kpis.tasaLetalidad}</b>
          </div>
        </div>

        {/* Options */}
        <div>
          {/* Excel */}
          <label

          >
            <input
              type="radio"
              name="exportFormat"
              value="excel"
              checked={selectedFormat === 'excel'}
              onChange={() => setSelectedFormat('excel')}

            />
            <div>📊</div>
            <div>
              <div>
                Libro de Excel (.xlsx) Multi-Hoja
              </div>
              <div>
                Incluye hojas estructuradas de KPIs, causas CIE-10, demoras, evolución mensual y edades.
              </div>
            </div>
          </label>

          {/* PDF */}
          <label

          >
            <input
              type="radio"
              name="exportFormat"
              value="pdf"
              checked={selectedFormat === 'pdf'}
              onChange={() => setSelectedFormat('pdf')}

            />
            <div>📄</div>
            <div>
              <div>
                Informe Ejecutivo en PDF (Membrete Médico)
              </div>
              <div>
                Documento formal formateado para impresión o guardado como PDF con análisis IA y tablas.
              </div>
            </div>
          </label>

          {/* CSV */}
          <label

          >
            <input
              type="radio"
              name="exportFormat"
              value="csv"
              checked={selectedFormat === 'csv'}
              onChange={() => setSelectedFormat('csv')}

            />
            <div>📁</div>
            <div>
              <div>
                Datos Planos en CSV (.csv)
              </div>
              <div>
                Exportación cruda para importación en R, Python, SPSS o visualizadores externos.
              </div>
            </div>
          </label>
        </div>

        {exportError && (
          <p role="alert">
            {exportError}
          </p>
        )}

        {/* Buttons */}
        <div>
          <button
            onClick={onClose}

          >
            Cancelar
          </button>
          <button
            onClick={handleExport}
            disabled={isExporting}

          >
            {isExporting ? 'Generando...' : 'Descargar Reporte'}
          </button>
        </div>
      </div>
    </div>
  )
}
