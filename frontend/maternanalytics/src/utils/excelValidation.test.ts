import { describe, it, expect } from 'vitest'
import * as XLSX from 'xlsx'
import { previewExcel } from './excelValidation'

function buildXlsxFile(rows: unknown[][], name = 'datos.xlsx'): File {
  const worksheet = XLSX.utils.aoa_to_sheet(rows)
  const workbook = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(workbook, worksheet, 'Hoja1')
  const buffer = XLSX.write(workbook, { type: 'array', bookType: 'xlsx' })
  return new File([buffer], name, { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
}

const requiredColumns = ['Nombres y apellidos', 'Tipo de ID']

describe('previewExcel', () => {
  it('extrae encabezados, hasta 5 filas y el total real de filas con datos', async () => {
    const rows = [
      ['Nombres y apellidos', 'Tipo de ID'],
      ...Array.from({ length: 8 }, (_, i) => [`Paciente ${i + 1}`, 'CC']),
    ]
    const file = buildXlsxFile(rows)

    const preview = await previewExcel(file, requiredColumns, 'morbilidad')

    expect(preview).not.toBeNull()
    expect(preview?.headers).toEqual(['Nombres y apellidos', 'Tipo de ID'])
    expect(preview?.rows).toHaveLength(5)
    expect(preview?.rows[0]).toEqual(['Paciente 1', 'CC'])
    expect(preview?.totalRows).toBe(8)
  })

  it('ignora filas completamente vacías al contar el total', async () => {
    const rows = [
      ['Nombres y apellidos', 'Tipo de ID'],
      ['Paciente 1', 'CC'],
      [undefined, undefined],
      ['Paciente 2', 'CE'],
    ]
    const file = buildXlsxFile(rows)

    const preview = await previewExcel(file, requiredColumns, 'morbilidad')

    expect(preview?.totalRows).toBe(2)
  })

  it('retorna null si la hoja está completamente vacía', async () => {
    const file = buildXlsxFile([])

    const preview = await previewExcel(file, requiredColumns, 'morbilidad')

    expect(preview).toBeNull()
  })
})
