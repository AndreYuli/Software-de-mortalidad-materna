export interface AnalisisMeta {
  id: number
  nombre_archivo: string
  fecha_carga: string
  limpieza_datos: Record<string, unknown>
  total_registros?: number
  anos_disponibles: number[]
  filtros_activos: { year: string | null; month: string | null }
  distribucion_mensual?: Record<string, Record<string, number>>
  causas_cie10?: { top_causas: CausaCie10[]; total_causas_unicas: number }
  criterios_inclusion?: Record<string, CriterioInclusion>
  demoras?: Record<string, DemoraDetalle>
}

export interface EstadisticasBasicas {
  total_casos?: number
  controles_prenatales_promedio?: number
  estancia_hospitalaria_promedio?: number
}

export interface CausaCie10 {
  codigo: string
  casos: number
}

export interface DemoraDetalle {
  nombre: string
  casos_con_demora: number
  porcentaje: number
}

export interface CriterioInclusion {
  nombre: string
  casos: number
  porcentaje: number
}

export interface IndicadoresMortalidad extends AnalisisMeta {
  tipo: 'mortalidad'
  estadisticas_basicas?: EstadisticasBasicas
  momento_muerte: Record<string, unknown>
  obstetrico_edad: Record<string, unknown>
}

export interface IndicadoresMorbilidad extends AnalisisMeta {
  tipo: 'morbilidad'
  estadisticas_basicas?: EstadisticasBasicas
  momento_ocurrencia: Record<string, unknown>
  institucion_referencia: Record<string, unknown>
  tiempo_remision: Record<string, unknown>
  obstetrico_edad: Record<string, unknown>
}

export type AnalisisCompleto = IndicadoresMortalidad | IndicadoresMorbilidad

export interface AnalisisResponse {
  id: number
  tipo: 'mortalidad' | 'morbilidad'
  nombre_archivo: string
  fecha_carga: string
  total_registros: number
}

export type TipoNarrativa = 'resumen_ejecutivo' | 'demoras' | 'clustering' | 'tendencias'

export interface FiltrosNarrativa {
  year?: string
  month?: string
  tipoClustering?: string
  nClusters?: number
}

export interface NarrativaResponse {
  narrativa: string
  modelo: string
  generado_en: string
  desde_cache: boolean
}
