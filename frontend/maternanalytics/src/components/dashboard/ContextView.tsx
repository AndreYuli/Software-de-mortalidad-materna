import type { ReactNode } from "react";
import {
  Activity,
  FileSpreadsheet,
  Shield,
  BarChart3,
  Stethoscope,
  ClipboardList,
} from "lucide-react";
import type { ActiveView } from "../../hooks/navigation/useActiveView";

interface ContextViewProps {
  onNavigate: (view: ActiveView) => void;
}

interface FeatureCard {
  icon: typeof Activity;
  title: string;
  children: ReactNode;
}

function FeatureCardView({ icon: Icon, title, children }: FeatureCard) {
  return (
    <div className="flex gap-3 rounded-xl border border-slate-200 bg-white p-4">
      <span className="flex size-10 shrink-0 items-center justify-center rounded-lg bg-brand-magenta/10 text-brand-magenta">
        <Icon className="size-5" aria-hidden="true" />
      </span>
      <div>
        <h3 className="text-sm font-semibold text-brand-deep">{title}</h3>
        <p className="mt-1 text-sm leading-relaxed text-slate-600">
          {children}
        </p>
      </div>
    </div>
  );
}

const PASOS = [
  {
    label: "1. Exporta",
    desc: "Descarga la plantilla o prepara tu archivo .xlsx con los campos del evento.",
  },
  {
    label: "2. Carga",
    desc: "Arrastra el archivo en «Carga de Datos». Validamos las columnas al instante.",
  },
  {
    label: "3. Analiza",
    desc: "El sistema calcula KPIs, causas, demoras y clustering.",
  },
  {
    label: "4. Explora",
    desc: "Visualiza el Dashboard, genera reportes y consulta al asistente IA.",
  },
];

export function ContextView({ onNavigate }: ContextViewProps) {
  return (
    <div className="mx-auto flex w-full max-w-3xl flex-col gap-6">
      <header className="flex flex-col gap-2">
        <span className="inline-flex w-fit items-center gap-1.5 rounded-full bg-brand-magenta/10 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-brand-magenta">
          <Stethoscope className="size-3.5" aria-hidden="true" />
          Contexto del proyecto
        </span>
        <h1 className="text-2xl font-bold leading-tight text-brand-deep">
          ¿Qué es Vida<span className="text-brand-magenta">Materna</span>?
        </h1>
        <p className="text-sm leading-relaxed text-slate-600">
          Es una plataforma de análisis epidemiológico para la vigilancia de la{" "}
          <b>mortalidad y morbilidad materna extrema</b>. Permite cargar los
          registros de los eventos del SIVIGILA (Colombia), calcular indicadores
          clave, detectar patrones con modelos de agrupamiento (clustering) y
          generar reportes para la toma de decisiones en salud pública.
        </p>
      </header>

      <section className="flex flex-col gap-3">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400">
          Los eventos que se vigilan
        </h2>
        <div className="grid gap-3 sm:grid-cols-2">
          <FeatureCardView
            icon={ClipboardList}
            title="Evento 550 · Mortalidad Materna"
          >
            Defunciones de mujeres durante el embarazo o hasta 42 días después
            de la terminación de la gestación. Registra causa básica CIE-10,
            sitio de defunción, demoras y antecedentes obstétricos.
          </FeatureCardView>
          <FeatureCardView
            icon={Activity}
            title="Evento 549 · Morbilidad Materna Extrema"
          >
            Complicaciones severas que pusieron en riesgo la vida de la madre
            (p. ej. eclampsia, sepsis, hemorragia obstétrica, ruptura uterina,
            ingreso a UCI). Se codifica con criterios clínicos.
          </FeatureCardView>
        </div>
      </section>

      <section className="flex flex-col gap-3">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400">
          ¿Qué obtienes al analizar?
        </h2>
        <div className="grid gap-3 sm:grid-cols-2">
          <FeatureCardView icon={BarChart3} title="Indicadores y tendencias">
            Casos totales, tasa de letalidad, evolución mensual y distribución
            por edad y riesgo, filtrables por año, mes y segmento.
          </FeatureCardView>
          <FeatureCardView icon={FileSpreadsheet} title="Reportes exportables">
            Exporta consolidados a Excel multi-hoja, informe ejecutivo en PDF
            con membrete médico o datos planos en CSV para herramientas
            estadísticas externas.
          </FeatureCardView>
        </div>
      </section>

      <section className="flex flex-col gap-3">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400">
          Cómo funciona, paso a paso
        </h2>
        <ol className="grid gap-3 sm:grid-cols-2">
          {PASOS.map((paso) => (
            <li
              key={paso.label}
              className="rounded-xl border border-slate-200 bg-white p-4"
            >
              <span className="text-sm font-semibold text-brand-magenta">
                {paso.label}
              </span>
              <p className="mt-1 text-sm text-slate-600">{paso.desc}</p>
            </li>
          ))}
        </ol>
      </section>

      <section className="flex gap-3 rounded-xl border border-slate-200 bg-slate-50 p-4">
        <span className="flex size-10 shrink-0 items-center justify-center rounded-lg bg-emerald-100 text-emerald-700">
          <Shield className="size-5" aria-hidden="true" />
        </span>
        <div>
          <h3 className="text-sm font-semibold text-brand-deep">
            Manejo responsable de datos
          </h3>
          <p className="mt-1 text-sm leading-relaxed text-slate-600">
            Los archivos cargados contienen información personal de salud. Su
            uso está limitado a la vigilancia epidemiológica institucional.
            Trata siempre los datos conforme a la normativa de protección de
            datos personales vigente en Colombia (Ley 1581 de 2012).
          </p>
        </div>
      </section>

      <div className="flex flex-col gap-2 sm:flex-row">
        <button
          type="button"
          onClick={() => onNavigate("mortalidad")}
          className="btn-primary-raised inline-flex items-center justify-center gap-2 rounded-lg px-5 py-2.5 text-sm font-semibold text-white"
        >
          Cargar datos ahora
        </button>
        <button
          type="button"
          onClick={() => onNavigate("analisis")}
          className="btn-raised inline-flex items-center justify-center gap-2 rounded-lg px-5 py-2.5 text-sm font-semibold text-slate-700"
        >
          Ir al Dashboard
        </button>
      </div>
    </div>
  );
}
