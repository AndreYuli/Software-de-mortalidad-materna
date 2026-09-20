import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { FilePreviewTable } from './FilePreviewTable'

describe('FilePreviewTable', () => {
  it('muestra el conteo de registros y columnas, y las filas de muestra', () => {
    const preview = {
      headers: ['Nombres y apellidos', 'Tipo de ID'],
      rows: [
        ['Paciente 1', 'CC'],
        ['Paciente 2', 'CE'],
      ],
      totalRows: 40,
    }
    render(<FilePreviewTable preview={preview} />)

    expect(screen.getByText(/40/)).toBeInTheDocument()
    expect(screen.getByText('registros detectados', { exact: false })).toBeInTheDocument()
    expect(screen.getByText('Nombres y apellidos')).toBeInTheDocument()
    expect(screen.getByText('Paciente 1')).toBeInTheDocument()
    expect(screen.getByText('CE')).toBeInTheDocument()
  })

  it('muestra un guion para celdas vacías', () => {
    const preview = {
      headers: ['Nombres y apellidos', 'Tipo de ID'],
      rows: [['Paciente 1', undefined]],
      totalRows: 1,
    }
    render(<FilePreviewTable preview={preview} />)

    expect(screen.getByText('—')).toBeInTheDocument()
  })

  it('no renderiza nada si no hay encabezados', () => {
    const preview = { headers: [], rows: [], totalRows: 0 }
    const { container } = render(<FilePreviewTable preview={preview} />)

    expect(container).toBeEmptyDOMElement()
  })
})
