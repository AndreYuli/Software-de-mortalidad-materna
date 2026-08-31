import { describe, it, expect, vi } from 'vitest'
import { render, fireEvent } from '@testing-library/react'
import { UploadCard } from './UploadCard'

function makeFile(name: string) {
  return new File(['contenido'], name, { type: 'application/vnd.ms-excel' })
}

describe('UploadCard', () => {
  it('llama a onFile al seleccionar un archivo', () => {
    const onFile = vi.fn()
    const { container } = render(
      <UploadCard onFile={onFile} onRemove={() => {}} eventLabel="Mortalidad" file={null} error={null} validating={false} />,
    )
    const input = container.querySelector('input[type="file"]') as HTMLInputElement
    fireEvent.change(input, { target: { files: [makeFile('datos.xlsx')] } })
    expect(onFile).toHaveBeenCalledTimes(1)
  })

  it('resetea el valor del input tras seleccionar, para poder re-seleccionar el mismo archivo', () => {
    const onFile = vi.fn()
    const { container } = render(
      <UploadCard onFile={onFile} onRemove={() => {}} eventLabel="Mortalidad" file={null} error={null} validating={false} />,
    )
    const input = container.querySelector('input[type="file"]') as HTMLInputElement
    fireEvent.change(input, { target: { files: [makeFile('datos.xlsx')] } })
    expect(input.value).toBe('')
  })
})
