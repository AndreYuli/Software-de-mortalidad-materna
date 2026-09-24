import type { FilePreview } from '../../utils/excelValidation'

export interface FilePreviewTableProps {
  preview: FilePreview
}

function formatCell(value: unknown): string {
  if (value === undefined || value === null || value === '') return '—'
  return String(value)
}

export function FilePreviewTable({ preview }: FilePreviewTableProps) {
  const { headers, rows, totalRows } = preview
  if (headers.length === 0) return null

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <p className="mb-3 text-sm text-slate-600">
        Vista previa: <strong>{totalRows}</strong> {totalRows === 1 ? 'registro detectado' : 'registros detectados'} ·{' '}
        {headers.length} {headers.length === 1 ? 'columna' : 'columnas'}
      </p>
      {rows.length > 0 && (
        <div className="overflow-x-auto rounded-lg border border-slate-200">
          <table className="w-full border-collapse text-left text-xs [&_td]:whitespace-nowrap [&_td]:border-t [&_td]:border-slate-100 [&_td]:px-3 [&_td]:py-2 [&_td]:text-slate-600 [&_th]:whitespace-nowrap [&_th]:bg-slate-50 [&_th]:px-3 [&_th]:py-2 [&_th]:font-semibold [&_th]:text-slate-500">
            <thead>
              <tr>
                {headers.map((header, i) => (
                  <th key={i}>{header || `Columna ${i + 1}`}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((row, rowIndex) => (
                <tr key={rowIndex}>
                  {headers.map((_, colIndex) => (
                    <td key={colIndex}>{formatCell(row[colIndex])}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
