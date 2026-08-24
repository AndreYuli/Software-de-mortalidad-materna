import * as XLSX from 'xlsx'
import { ALIAS_COLUMNAS } from '../constants/dashboardConstants'

export type TipoEvento = 'morbilidad' | 'mortalidad'

export interface FileValidationError {
  parseError?: boolean
  missing?: string[]
  found?: string[]
}

export function normalizeHeader(value: unknown): string {
  return String(value ?? '')
    .trim()
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/n°|nº/g, 'n ')
    .replaceAll('no.', 'n ')
    .replace(/no\s+/g, 'n ')
    .replace(/[^a-z0-9]+/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
}

export function buildAliasMap(requiredColumns: string[], tipo: TipoEvento): Map<string, string> {
  const aliasMap = new Map(requiredColumns.map((column) => [normalizeHeader(column), column]))
  Object.entries(ALIAS_COLUMNAS[tipo] || {}).forEach(([canonical, aliases]) => {
    aliasMap.set(normalizeHeader(canonical), canonical)
    aliases.forEach((alias) => aliasMap.set(normalizeHeader(alias), canonical))
  })
  return aliasMap
}

export function findHeaderRow(jsonData: unknown[][], requiredColumns: string[], tipo: TipoEvento): number {
  const aliasMap = buildAliasMap(requiredColumns, tipo)
  let bestIndex = 0
  let bestScore = -1

  jsonData.slice(0, 5).forEach((row, index) => {
    const matchedHeaders = new Set(
      row
        .map((header) => aliasMap.get(normalizeHeader(header)))
        .filter(Boolean),
    )

    if (matchedHeaders.size > bestScore) {
      bestIndex = index
      bestScore = matchedHeaders.size
    }
  })

  return bestIndex
}

export function findBestSheet(workbook: XLSX.WorkBook, requiredColumns: string[], tipo: TipoEvento): string {
  let bestSheet = workbook.SheetNames[0]
  let bestScore = -1

  workbook.SheetNames.forEach((sheetName) => {
    const sheet = workbook.Sheets[sheetName]
    const jsonData: unknown[][] = XLSX.utils.sheet_to_json(sheet, { header: 1 })
    const headerRowIndex = findHeaderRow(jsonData, requiredColumns, tipo)
    const aliasMap = buildAliasMap(requiredColumns, tipo)
    const headers = ((jsonData[headerRowIndex] as unknown[]) || []).map((header) => String(header ?? '').trim())
    const matchedHeaders = new Set(
      headers
        .map((header) => aliasMap.get(normalizeHeader(header)))
        .filter(Boolean),
    )

    if (matchedHeaders.size > bestScore) {
      bestSheet = sheetName
      bestScore = matchedHeaders.size
    }
  })

  return bestSheet
}

export async function validateColumns(
  file: File,
  requiredColumns: string[],
  tipo: TipoEvento,
): Promise<{ valid: true } | ({ valid: false } & FileValidationError)> {
  try {
    const buffer = await file.arrayBuffer()
    const workbook = XLSX.read(new Uint8Array(buffer), { type: 'array', sheetRows: 10 })
    const bestSheetName = findBestSheet(workbook, requiredColumns, tipo)
    const jsonData: unknown[][] = XLSX.utils.sheet_to_json(workbook.Sheets[bestSheetName], { header: 1 })

    if (jsonData.length === 0) {
      return { valid: false, parseError: true }
    }

    const headerRowIndex = findHeaderRow(jsonData, requiredColumns, tipo)
    const headers = ((jsonData[headerRowIndex] as unknown[]) || []).map((header) => String(header ?? '').trim())
    const aliasMap = buildAliasMap(requiredColumns, tipo)
    const normalizedHeaders = new Set(
      headers
        .map((header) => aliasMap.get(normalizeHeader(header)))
        .filter(Boolean),
    )
    const missing = requiredColumns.filter(
      (column) => !normalizedHeaders.has(column),
    )

    return missing.length > 0
      ? { valid: false, missing, found: headers }
      : { valid: true }
  } catch {
    return { valid: false, parseError: true }
  }
}
