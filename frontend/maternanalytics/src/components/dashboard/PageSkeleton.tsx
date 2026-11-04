/** Marcador de carga: ocupa el espacio de la página y avisa a lectores de pantalla. */
export function PageSkeleton() {
  return (
    <div role="status" aria-busy="true" className="mx-auto w-full max-w-5xl animate-pulse space-y-4 p-6">
      <span className="sr-only">Cargando…</span>
      <div className="h-8 w-1/3 rounded-lg bg-slate-200" />
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {Array.from({ length: 4 }, (_, i) => (
          <div key={i} className="h-24 rounded-xl bg-slate-200" />
        ))}
      </div>
      <div className="h-64 rounded-xl bg-slate-200" />
    </div>
  );
}
