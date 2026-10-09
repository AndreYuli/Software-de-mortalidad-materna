import { MapPin } from "lucide-react";
import { municipioDeSecretaria } from "../../constants/authConstants";

interface SecretariaBadgeProps {
  /** Nombre completo de la secretaría (ej. «Secretaría de Salud de Bello»). */
  secretaria?: string | null;
  className?: string;
}

/**
 * Indicador visual compacto del municipio/secretaría del usuario autenticado.
 * No se renderiza si no hay secretaría conocida (cuentas antiguas sin tenant).
 */
export function SecretariaBadge({
  secretaria,
  className = "",
}: SecretariaBadgeProps) {
  const municipio = municipioDeSecretaria(secretaria);
  if (!municipio) return null;

  return (
    <span
      title={secretaria ?? municipio}
      aria-label={`Secretaría de salud: ${secretaria ?? municipio}`}
      className={`inline-flex items-center gap-1 rounded-full bg-brand-magenta/10 px-2.5 py-1 text-xs font-medium text-brand-deep ${className}`}
    >
      <MapPin
        className="size-3.5 shrink-0 text-brand-magenta"
        aria-hidden="true"
      />
      <span className="truncate">{municipio}</span>
    </span>
  );
}
