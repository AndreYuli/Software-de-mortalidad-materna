export interface DashboardErrorStateProps {
  message: string
}

export function DashboardErrorState({ message }: DashboardErrorStateProps) {
  return (
    <div style={{ padding: '24px', background: '#fef2f2', borderRadius: '12px', border: '1px solid #fee2e2', color: '#b91c1c', textAlign: 'center' }}>
      <p style={{ fontWeight: '600', margin: '0 0 12px' }}>❌ {message}</p>
      <button onClick={() => window.location.reload()} className="primary-action-btn">
        Reintentar
      </button>
    </div>
  )
}
