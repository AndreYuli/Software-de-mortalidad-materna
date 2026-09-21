const LINE_HEIGHT = 20
const MIN_BAR_HEIGHT = 8
const AXIS_PADDING = 60
const MIN_CHART_HEIGHT = 320

export const wrapLabel = (text: string, maxLen: number = 45): string | string[] => {
  if (text.length <= maxLen) return text
  const words = text.split(' ')
  const lines: string[] = []
  let currentLine = ''
  for (const word of words) {
    if ((currentLine + word).length > maxLen) {
      if (currentLine) lines.push(currentLine.trim())
      currentLine = word + ' '
    } else {
      currentLine += word + ' '
    }
  }
  if (currentLine) lines.push(currentLine.trim())
  return lines
}

export const calculateChartHeight = (labels: string[]): number => {
  if (labels.length === 0) return MIN_CHART_HEIGHT
  const totalBarsHeight = labels.reduce((sum, label) => {
    const wrapped = wrapLabel(label)
    const lineCount = Array.isArray(wrapped) ? wrapped.length : 1
    return sum + MIN_BAR_HEIGHT + lineCount * LINE_HEIGHT
  }, 0)
  return Math.max(MIN_CHART_HEIGHT, AXIS_PADDING + totalBarsHeight)
}
