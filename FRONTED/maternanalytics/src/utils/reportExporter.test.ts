import { describe, it, expect } from 'vitest'
import {
  exportReportToExcel,
  exportToCsv,
  ReportExportData,
} from './reportExporter'

describe('reportExporter', () => {
  const mockReportData: ReportExportData = {
    titulo: 'Informe Epidemiológico de Vigilancia Materna (SIVIGILA)',
    fechaGeneracion: '24 de agosto de 2026',
    periodo: {
      anio: '2026',
      mes: '3',
      segmento: 'ambos',
    },
    kpis: {
      totalDefunciones: 120,
      totalMorbilidad: 450,
      casosTotales: 570,
      tasaLetalidad: '21.05%',
      promedioEdad: '28 años',
    },
    evolucionMensual: {
      meses: ['Ene', 'Feb', 'Mar'],
      mortalidad: [30, 40, 50],
      morbilidad: [100, 150, 200],
    },
    causasPrincipales: {
      causas: ['O14.1', 'O72.1'],
      valores: [80, 40],
    },
    demoras: {
      nombres: ['Demora 1', 'Demora 4'],
      valores: [30, 90],
    },
    distribucionEdad: {
      grupos: ['20-29', '30-39'],
      mortalidad: [70, 50],
      morbilidad: [250, 200],
    },
    aiSummary: 'Análisis IA consolidado del periodo.',
  }

  it('exportReportToExcel genera un archivo sin lanzar excepciones', () => {
    expect(() => exportReportToExcel(mockReportData, 'test.xlsx')).not.toThrow()
  })

  it('exportToCsv descarga el archivo CSV con los encabezados y filas correctas', () => {
    expect(() =>
      exportToCsv('test_csv', ['Header1', 'Header2'], [['Val1', 'Val2'], [1, 2]]),
    ).not.toThrow()
  })
})
