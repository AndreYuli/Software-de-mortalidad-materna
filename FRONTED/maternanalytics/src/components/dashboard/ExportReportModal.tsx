import React, { useState } from 'react'
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

  if (!isOpen) return null

  const handleExport = () => {
    setIsExporting(true)
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
      setIsExporting(false)
    }
  }

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(15, 23, 42, 0.65)',
        backdropFilter: 'blur(4px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 9999,
        padding: '20px',
      }}
      onClick={onClose}
    >
      <div
        style={{
          background: '#ffffff',
          borderRadius: '18px',
          width: '100%',
          maxWidth: '520px',
          padding: '28px',
          boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1)',
          border: '1px solid #e2e8f0',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '18px' }}>
          <div>
            <h2 style={{ margin: '0 0 4px 0', fontSize: '18px', fontWeight: 800, color: '#0f172a' }}>
              Exportar Reporte Epidemiológico
            </h2>
            <p style={{ margin: 0, fontSize: '13px', color: '#64748b' }}>
              Selecciona el formato de exportación para los datos consolidados.
            </p>
          </div>
          <button
            onClick={onClose}
            style={{
              background: '#f1f5f9',
              border: 'none',
              borderRadius: '50%',
              width: '32px',
              height: '32px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#64748b',
              fontWeight: 700,
            }}
          >
            ✕
          </button>
        </div>

        {/* Info resumen */}
        <div
          style={{
            background: '#f8fafc',
            border: '1px solid #e2e8f0',
            borderRadius: '12px',
            padding: '12px 16px',
            marginBottom: '20px',
            fontSize: '12.5px',
            color: '#334155',
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            gap: '8px',
          }}
        >
          <div>
            <span style={{ color: '#64748b' }}>Periodo: </span>
            <b>{reportData.periodo.anio || 'Histórico'} {reportData.periodo.mes ? `(Mes ${reportData.periodo.mes})` : ''}</b>
          </div>
          <div>
            <span style={{ color: '#64748b' }}>Segmento: </span>
            <b>{reportData.periodo.segmento.toUpperCase()}</b>
          </div>
          <div>
            <span style={{ color: '#64748b' }}>Total Casos: </span>
            <b>{reportData.kpis.casosTotales}</b>
          </div>
          <div>
            <span style={{ color: '#64748b' }}>Razón: </span>
            <b>{reportData.kpis.tasaLetalidad}</b>
          </div>
        </div>

        {/* Options */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginBottom: '24px' }}>
          {/* Excel */}
          <label
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '14px',
              padding: '14px 16px',
              borderRadius: '12px',
              border: selectedFormat === 'excel' ? '2px solid #10b981' : '1.5px solid #e2e8f0',
              background: selectedFormat === 'excel' ? '#ecfdf5' : '#ffffff',
              cursor: 'pointer',
              transition: 'all 0.2s ease',
            }}
          >
            <input
              type="radio"
              name="exportFormat"
              value="excel"
              checked={selectedFormat === 'excel'}
              onChange={() => setSelectedFormat('excel')}
              style={{ width: '16px', height: '16px', accentColor: '#10b981' }}
            />
            <div style={{ fontSize: '24px' }}>📊</div>
            <div style={{ flex: 1 }}>
              <div style={{ fontWeight: 700, fontSize: '13.5px', color: '#0f172a' }}>
                Libro de Excel (.xlsx) Multi-Hoja
              </div>
              <div style={{ fontSize: '12px', color: '#64748b' }}>
                Incluye hojas estructuradas de KPIs, causas CIE-10, demoras, evolución mensual y edades.
              </div>
            </div>
          </label>

          {/* PDF */}
          <label
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '14px',
              padding: '14px 16px',
              borderRadius: '12px',
              border: selectedFormat === 'pdf' ? '2px solid #3b82f6' : '1.5px solid #e2e8f0',
              background: selectedFormat === 'pdf' ? '#eff6ff' : '#ffffff',
              cursor: 'pointer',
              transition: 'all 0.2s ease',
            }}
          >
            <input
              type="radio"
              name="exportFormat"
              value="pdf"
              checked={selectedFormat === 'pdf'}
              onChange={() => setSelectedFormat('pdf')}
              style={{ width: '16px', height: '16px', accentColor: '#3b82f6' }}
            />
            <div style={{ fontSize: '24px' }}>📄</div>
            <div style={{ flex: 1 }}>
              <div style={{ fontWeight: 700, fontSize: '13.5px', color: '#0f172a' }}>
                Informe Ejecutivo en PDF (Membrete Médico)
              </div>
              <div style={{ fontSize: '12px', color: '#64748b' }}>
                Documento formal formateado para impresión o guardado como PDF con análisis IA y tablas.
              </div>
            </div>
          </label>

          {/* CSV */}
          <label
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '14px',
              padding: '14px 16px',
              borderRadius: '12px',
              border: selectedFormat === 'csv' ? '2px solid #8b5cf6' : '1.5px solid #e2e8f0',
              background: selectedFormat === 'csv' ? '#f5f3ff' : '#ffffff',
              cursor: 'pointer',
              transition: 'all 0.2s ease',
            }}
          >
            <input
              type="radio"
              name="exportFormat"
              value="csv"
              checked={selectedFormat === 'csv'}
              onChange={() => setSelectedFormat('csv')}
              style={{ width: '16px', height: '16px', accentColor: '#8b5cf6' }}
            />
            <div style={{ fontSize: '24px' }}>📁</div>
            <div style={{ flex: 1 }}>
              <div style={{ fontWeight: 700, fontSize: '13.5px', color: '#0f172a' }}>
                Datos Planos en CSV (.csv)
              </div>
              <div style={{ fontSize: '12px', color: '#64748b' }}>
                Exportación cruda para importación en R, Python, SPSS o visualizadores externos.
              </div>
            </div>
          </label>
        </div>

        {/* Buttons */}
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
          <button
            onClick={onClose}
            style={{
              padding: '10px 18px',
              borderRadius: '10px',
              border: '1px solid #cbd5e1',
              background: '#ffffff',
              color: '#475569',
              fontWeight: 600,
              fontSize: '13px',
              cursor: 'pointer',
            }}
          >
            Cancelar
          </button>
          <button
            onClick={handleExport}
            disabled={isExporting}
            style={{
              padding: '10px 22px',
              borderRadius: '10px',
              border: 'none',
              background: 'linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%)',
              color: '#ffffff',
              fontWeight: 700,
              fontSize: '13px',
              cursor: 'pointer',
              boxShadow: '0 4px 6px -1px rgba(37, 99, 235, 0.25)',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
            }}
          >
            {isExporting ? 'Generando...' : 'Descargar Reporte'}
          </button>
        </div>
      </div>
    </div>
  )
}
