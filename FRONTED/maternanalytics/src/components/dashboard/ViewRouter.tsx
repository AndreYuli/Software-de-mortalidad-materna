import type { ActiveView } from '../../hooks/navigation/useActiveView'
import type { DashboardData } from '../../hooks/useDashboardData'
import { AnalysisHomeSection } from './AnalysisHomeSection'
import { UploadSection } from './UploadSection'

export interface ViewRouterProps {
  activeView: ActiveView
  data: DashboardData
  onNavigate: (view: ActiveView) => void
}

export function ViewRouter({ activeView, data, onNavigate }: ViewRouterProps) {
  switch (activeView) {
    case 'analisis':
      return (
        <AnalysisHomeSection
          latestMortalidad={data.latestMortalidad}
          latestMorbilidad={data.latestMorbilidad}
          onGoToUpload={onNavigate}
          filterYear={data.filterYear}
          filterMonth={data.filterMonth}
          availableYears={data.availableYears}
          onAvailableYears={data.setAvailableYears}
          onYearChange={data.setFilterYear}
          onMonthChange={data.setFilterMonth}
        />
      )

    case 'mortalidad':
      return (
        <UploadSection
          title="Cargar Datos de Mortalidad Materna"
          description="Sube el archivo Excel con los registros del Evento 550. Validaremos la estructura de las columnas automáticamente."
          eventLabel="Mortalidad Materna (Evento 550)"
          file={data.mortalidadFile}
          error={data.mortalidadError}
          validating={data.mortalidadValidating}
          done={data.mortalidadDone}
          analyzeError={data.mortalidadAnalyzeError}
          analyzing={data.analyzing}
          actionLabel="Iniciar análisis"
          onFile={data.handleMortalidadFile}
          onAnalyze={data.handleAnalyzeMortalidad}
        />
      )

    case 'morbilidad':
      return (
        <UploadSection
          title="Cargar Datos de Morbilidad Materna Extrema"
          description="Sube el archivo Excel con los registros del Evento 549. Validaremos la estructura de las columnas automáticamente."
          eventLabel="Morbilidad Materna Extrema (Evento 549)"
          file={data.morbilidadFile}
          error={data.morbilidadError}
          validating={data.morbilidadValidating}
          done={data.morbilidadDone}
          analyzeError={data.morbilidadAnalyzeError}
          analyzing={data.analyzing}
          actionLabel="Iniciar análisis"
          onFile={data.handleMorbilidadFile}
          onAnalyze={data.handleAnalyzeMorbilidad}
        />
      )

    default: {
      const _exhaustiveCheck: never = activeView;
      return _exhaustiveCheck;
    }
  }
}
