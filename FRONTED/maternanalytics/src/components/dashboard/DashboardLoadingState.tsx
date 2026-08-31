import '../shared/Spinner.css'

export function DashboardLoadingState() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '400px' }}>
      <div className="spinner"></div>
      <p style={{ marginTop: '16px', color: '#64748b', fontWeight: '600' }}>
        Generando panel estratégico...
      </p>
    </div>
  )
}
