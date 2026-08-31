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
    <div className="upload-preview-card">
      <p className="upload-preview-summary">
        Vista previa: <strong>{totalRows}</strong> {totalRows === 1 ? 'registro detectado' : 'registros detectados'} ·{' '}
        {headers.length} {headers.length === 1 ? 'columna' : 'columnas'}
      </p>
      {rows.length > 0 && (
        <div className="upload-preview-table-wrapper">
          <table className="upload-preview-table">
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
