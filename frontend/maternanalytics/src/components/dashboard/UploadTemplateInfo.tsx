import { useState } from "react";
import { ChevronDown, Info, FileSpreadsheet } from "lucide-react";
import {
  ALIAS_COLUMNAS,
  PLANTILLAS,
  TIPOS_CAMPO,
} from "../../constants/dashboardConstants";
import type { TipoEvento } from "../../utils/excelValidation";

type Props = { requiredColumns: string[]; tipo: TipoEvento };

const BADGE_STYLES: Record<string, string> = {
  Texto: "bg-slate-100 text-slate-600",
  Número: "bg-blue-100 text-blue-700",
  "Número entero": "bg-blue-100 text-blue-700",
  Fecha: "bg-amber-100 text-amber-700",
  Categórica: "bg-violet-100 text-violet-700",
  Booleana: "bg-emerald-100 text-emerald-700",
  "Código CIE-10": "bg-rose-100 text-rose-700",
};

export function UploadTemplateInfo({ requiredColumns, tipo }: Props) {
  const [expanded, setExpanded] = useState(false);
  const plantilla = PLANTILLAS[tipo];
  const tipos = TIPOS_CAMPO[tipo] || {};
  const alias = ALIAS_COLUMNAS[tipo] || {};
  const base = import.meta.env.BASE_URL || "/";
  const href = `${base}plantillas/${plantilla.archivo}`;

  return (
    <div className="rounded-xl border border-slate-200 bg-white shadow-sm">
      <button
        type="button"
        onClick={() => setExpanded((v) => !v)}
        className="flex w-full items-center justify-between gap-3 px-5 py-4 text-left transition-colors hover:bg-slate-50"
      >
        <span className="flex items-center gap-2.5">
          <Info className="h-4 w-4 shrink-0 text-[#971356]" />
          <span>
            <span className="block text-sm font-semibold text-slate-800">
              ¿Qué campos debe tener mi archivo?
            </span>
            <span className="block text-xs text-slate-500">
              Plantilla oficial ({plantilla.nombre}) · {requiredColumns.length}{" "}
              campos mínimos requeridos
            </span>
          </span>
        </span>
        <ChevronDown
          className={`h-4 w-4 shrink-0 text-slate-400 transition-transform ${expanded ? "rotate-180" : ""}`}
        />
      </button>

      {expanded && (
        <div className="border-t border-slate-100 px-5 py-4">
          <p className="mb-3 text-xs leading-relaxed text-slate-600">
            Descarga la <strong>plantilla oficial</strong>: la hoja{" "}
            <strong>PLANTILLA</strong> trae todas las columnas de la ficha con
            filas de ejemplo, y la hoja <strong>DICCIONARIO</strong> define el
            tipo de dato y las opciones válidas de cada campo. Para que el
            sistema acepte el archivo debe contener, como mínimo, estas columnas
            (puede traer muchas más):
          </p>

          <a
            href={href}
            download={plantilla.archivo}
            className="btn-primary-raised mb-4 inline-flex items-center gap-2 rounded-lg px-3.5 py-2 text-sm font-semibold text-white"
          >
            <FileSpreadsheet className="h-4 w-4" />
            Descargar plantilla oficial (.xlsx)
          </a>

          <div className="grid gap-2 sm:grid-cols-2">
            {requiredColumns.map((column, i) => {
              const info = tipos[column];
              const badge = info
                ? BADGE_STYLES[info.tipo] || "bg-slate-100 text-slate-600"
                : "";
              const variants = alias[column];
              return (
                <div
                  key={column}
                  className="rounded-lg border border-slate-100 bg-slate-50/70 px-3 py-2"
                >
                  <div className="flex items-start justify-between gap-2">
                    <span className="text-xs font-medium text-slate-700">
                      <span className="mr-1 text-slate-400">{i + 1}.</span>
                      {column}
                    </span>
                    {info && (
                      <span
                        className={`shrink-0 rounded-full px-2 py-0.5 text-[10px] font-semibold ${badge}`}
                      >
                        {info.tipo}
                      </span>
                    )}
                  </div>
                  {info?.opciones && (
                    <p className="mt-1 text-[11px] leading-snug text-slate-500">
                      {info.opciones}
                    </p>
                  )}
                  {variants && variants.length > 0 && (
                    <p className="mt-1 text-[11px] leading-snug text-slate-400">
                      Acepta también: {variants.join(", ")}
                    </p>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
