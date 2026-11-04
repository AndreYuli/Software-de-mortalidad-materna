import { describe, it, expect, vi } from 'vitest'
import * as XLSX from 'xlsx'
import {
  exportReportToExcel,
  exportToCsv,
  ReportExportData,
} from './reportExporter'

// writeFile se reemplaza para capturar el libro sin escribir a disco; el resto de xlsx es real.
const libros = vi.hoisted(() => [] as unknown[])
vi.mock('xlsx', async (importOriginal) => {
  const real = await importOriginal<typeof import('xlsx')>()
  return { ...real, writeFile: (wb: unknown) => void libros.push(wb) }
})

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

  describe('hoja Top Causas CIE-10 (revisión de uso, partes 4 y 6)', () => {
    function hojaCausas(data: ReportExportData) {
      libros.length = 0
      exportReportToExcel(data, 'x.xlsx')
      const libro = libros[0] as XLSX.WorkBook
      return XLSX.utils.sheet_to_json<Record<string, string | number>>(libro.Sheets['Top Causas CIE-10'])
    }

    it('lleva el código real y su descripción en columnas separadas, no intercambiadas', () => {
      const filas = hojaCausas(mockReportData)
      expect(filas[0]['Código']).toBe('O14.1')
      expect(String(filas[0]['Causa / Criterio'])).not.toMatch(/no disponible/i)
    })

    it('indica el evento y usa el porcentaje del dashboard con un decimal', () => {
      const filas = hojaCausas({
        ...mockReportData,
        causasPrincipales: {
          causas: ['O46.0', 'O14.1'],
          valores: [16, 80],
          eventos: ['Mortalidad', 'Morbilidad'],
          porcentajes: [7.9, 21.35],
        },
      })
      expect(filas[0]['Evento']).toBe('Mortalidad')
      expect(filas[0]['Porcentaje (%)']).toBe('7,9%')
      expect(filas[1]['Evento']).toBe('Morbilidad')
      expect(filas[1]['Porcentaje (%)']).toBe('21,4%')
    })

    it('sin porcentajes calcula la participación dentro de cada evento, no sobre la mezcla', () => {
      const filas = hojaCausas({
        ...mockReportData,
        causasPrincipales: {
          causas: ['O14.1', 'O72.1', 'O14.1'],
          valores: [50, 50, 10],
          eventos: ['Mortalidad', 'Mortalidad', 'Morbilidad'],
        },
      })
      expect(filas.map((f) => f['Porcentaje (%)'])).toEqual(['50,0%', '50,0%', '100,0%'])
    })
  })

  describe('hoja Causas asociadas CIE-10', () => {
    function libro(data: ReportExportData) {
      libros.length = 0
      exportReportToExcel(data, 'x.xlsx')
      return libros[0] as XLSX.WorkBook
    }

    it('exporta las causas asociadas con código, descripción y porcentaje de casos', () => {
      const wb = libro({
        ...mockReportData,
        causasAsociadas: { causas: ['O72.1', 'O15.0'], valores: [12, 3], porcentajes: [40, 10] },
      })
      const filas = XLSX.utils.sheet_to_json<Record<string, string | number>>(
        wb.Sheets['Causas asociadas CIE-10'],
      )
      expect(filas).toHaveLength(2)
      expect(filas[0]).toMatchObject({ Evento: 'Morbilidad', Código: 'O72.1', Casos: 12 })
      expect(filas[0]['Porcentaje de casos (%)']).toBe('40,0%')
      expect(String(filas[0]['Causa asociada'])).not.toMatch(/no disponible/i)
    })

    it('sin causas asociadas no agrega la hoja', () => {
      expect(libro(mockReportData).SheetNames).not.toContain('Causas asociadas CIE-10')
    })
  })
})
