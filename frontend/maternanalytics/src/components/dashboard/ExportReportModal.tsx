import React, { useEffect, useState } from "react";
import {
  exportReportToExcel,
  exportToCsv,
  printExecutiveMedicalReport,
  ReportExportData,
} from "../../utils/reportExporter";

export interface ExportReportModalProps {
  isOpen: boolean;
  onClose: () => void;
  reportData: ReportExportData;
}

export const ExportReportModal: React.FC<ExportReportModalProps> = ({
  isOpen,
  onClose,
  reportData,
}) => {
  const [selectedFormat, setSelectedFormat] = useState<"excel" | "pdf" | "csv">(
    "excel",
  );
  const [isExporting, setIsExporting] = useState(false);
  const [exportError, setExportError] = useState<string | null>(null);

  useEffect(() => {
    if (!isOpen) return;
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const handleExport = () => {
    setIsExporting(true);
    setExportError(null);
    try {
      if (selectedFormat === "excel") {
        exportReportToExcel(reportData);
      } else if (selectedFormat === "pdf") {
        printExecutiveMedicalReport(reportData);
      } else if (selectedFormat === "csv") {
        const headers = ["Diagnóstico CIE-10", "Casos"];
        const rows = reportData.causasPrincipales.causas.map((c, i) => [
          c,
          reportData.causasPrincipales.valores[i] || 0,
        ]);
        exportToCsv(
          `Causas_CIE10_${reportData.periodo.anio || "Consolidado"}`,
          headers,
          rows,
        );
      }
      setTimeout(() => {
        setIsExporting(false);
        onClose();
      }, 400);
    } catch (err) {
      console.error("Error al exportar reporte:", err);
      setExportError(
        "No se pudo generar el reporte. Intenta de nuevo o elige otro formato.",
      );
      setIsExporting(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 p-4"
      onClick={onClose}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-label="Exportar reporte epidemiológico"
        className="flex max-h-[90vh] w-full max-w-lg flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex-1 overflow-y-auto">
          {/* Header */}
          <div className="flex items-start justify-between gap-3 border-b border-slate-100 px-5 py-4">
            <div>
              <h2 className="text-lg font-bold text-brand-deep">
                Exportar Reporte Epidemiológico
              </h2>
              <p className="mt-0.5 text-sm text-slate-500">
                Selecciona el formato de exportación para los datos
                consolidados.
              </p>
            </div>
            <button
              onClick={onClose}
              type="button"
              aria-label="Cerrar"
              className="shrink-0 rounded-lg p-1.5 text-slate-400 transition hover:bg-slate-100 hover:text-slate-700"
            >
              ✕
            </button>
          </div>

          <div className="px-5 py-4">
            {/* Info resumen */}
            <div className="mb-4 grid grid-cols-2 gap-2 rounded-xl bg-slate-50 p-3 text-sm sm:grid-cols-4">
              <div className="flex flex-col">
                <span className="text-xs text-slate-400">Periodo</span>
                <b className="text-slate-700">
                  {reportData.periodo.anio || "Histórico"}{" "}
                  {reportData.periodo.mes
                    ? `(Mes ${reportData.periodo.mes})`
                    : ""}
                </b>
              </div>
              <div className="flex flex-col">
                <span className="text-xs text-slate-400">Segmento</span>
                <b className="text-slate-700">
                  {reportData.periodo.segmento.toUpperCase()}
                </b>
              </div>
              <div className="flex flex-col">
                <span className="text-xs text-slate-400">Total Casos</span>
                <b className="text-slate-700">{reportData.kpis.casosTotales}</b>
              </div>
              <div className="flex flex-col">
                <span className="text-xs text-slate-400">Letalidad</span>
                <b className="text-slate-700">
                  {reportData.kpis.tasaLetalidad}
                </b>
              </div>
            </div>

            {/* Options */}
            <div className="flex flex-col gap-2">
              {/* Excel */}
              <label
                className={`flex cursor-pointer items-start gap-3 rounded-xl border p-3 transition ${
                  selectedFormat === "excel"
                    ? "border-brand-magenta bg-brand-magenta/5 ring-1 ring-brand-magenta/30"
                    : "border-slate-200 hover:border-slate-300"
                }`}
              >
                <input
                  type="radio"
                  name="exportFormat"
                  value="excel"
                  checked={selectedFormat === "excel"}
                  onChange={() => setSelectedFormat("excel")}
                  className="mt-1 accent-brand-magenta"
                />
                <div className="text-xl leading-none">📊</div>
                <div>
                  <div className="text-sm font-semibold text-slate-800">
                    Libro de Excel (.xlsx) Multi-Hoja
                  </div>
                  <div className="text-xs text-slate-500">
                    Incluye hojas estructuradas de KPIs, causas CIE-10, demoras,
                    evolución mensual y edades.
                  </div>
                </div>
              </label>

              {/* PDF */}
              <label
                className={`flex cursor-pointer items-start gap-3 rounded-xl border p-3 transition ${
                  selectedFormat === "pdf"
                    ? "border-brand-magenta bg-brand-magenta/5 ring-1 ring-brand-magenta/30"
                    : "border-slate-200 hover:border-slate-300"
                }`}
              >
                <input
                  type="radio"
                  name="exportFormat"
                  value="pdf"
                  checked={selectedFormat === "pdf"}
                  onChange={() => setSelectedFormat("pdf")}
                  className="mt-1 accent-brand-magenta"
                />
                <div className="text-xl leading-none">📄</div>
                <div>
                  <div className="text-sm font-semibold text-slate-800">
                    Informe Ejecutivo en PDF (Membrete Médico)
                  </div>
                  <div className="text-xs text-slate-500">
                    Documento formal formateado para impresión o guardado como
                    PDF con análisis IA y tablas.
                  </div>
                </div>
              </label>

              {/* CSV */}
              <label
                className={`flex cursor-pointer items-start gap-3 rounded-xl border p-3 transition ${
                  selectedFormat === "csv"
                    ? "border-brand-magenta bg-brand-magenta/5 ring-1 ring-brand-magenta/30"
                    : "border-slate-200 hover:border-slate-300"
                }`}
              >
                <input
                  type="radio"
                  name="exportFormat"
                  value="csv"
                  checked={selectedFormat === "csv"}
                  onChange={() => setSelectedFormat("csv")}
                  className="mt-1 accent-brand-magenta"
                />
                <div className="text-xl leading-none">📁</div>
                <div>
                  <div className="text-sm font-semibold text-slate-800">
                    Datos Planos en CSV (.csv)
                  </div>
                  <div className="text-xs text-slate-500">
                    Exportación cruda para importación en R, Python, SPSS o
                    visualizadores externos.
                  </div>
                </div>
              </label>
            </div>

            {exportError && (
              <p
                role="alert"
                className="mt-3 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800"
              >
                {exportError}
              </p>
            )}
          </div>
        </div>

        {/* Buttons */}
        <div className="flex items-center justify-end gap-3 border-t border-slate-100 bg-slate-50 px-5 py-4">
          <button
            onClick={onClose}
            type="button"
            className="btn-raised rounded-lg px-4 py-2 text-sm font-semibold text-slate-700"
          >
            Cancelar
          </button>
          <button
            onClick={handleExport}
            disabled={isExporting}
            type="button"
            className="btn-primary-raised inline-flex items-center justify-center gap-2 rounded-lg px-5 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-50 disabled:saturate-50"
          >
            {isExporting ? "Generando..." : "Descargar Reporte"}
          </button>
        </div>
      </div>
    </div>
  );
};
