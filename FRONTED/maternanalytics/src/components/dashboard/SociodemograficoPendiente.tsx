export interface SociodemograficoPendienteProps {
  evento: 'Morbilidad' | 'Mortalidad'
}

export function SociodemograficoPendiente({ evento }: SociodemograficoPendienteProps) {
  return (
    <div className="tab-placeholder">
      <h3>Factores Sociodemográficos de {evento}</h3>
      <p>
        Esta sección está en construcción: las variables de zona, etnia, estrato
        socioeconómico, afiliación al sistema de salud y población vulnerable aún
        no están disponibles en los datos cargados.
      </p>
    </div>
  )
}
