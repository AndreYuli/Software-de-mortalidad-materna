import './dashboard/DashboardShell.css'
import { useDashboardData } from '../hooks/useDashboardData'
import { Sidebar, type DashboardFileStatus, type FileIndicator } from './dashboard/Sidebar'
import { ViewRouter } from './dashboard/ViewRouter'

export type { DashboardFileStatus, FileIndicator }

export interface DashboardOKDProps {
  onLogout: () => void
}

export default function DashboardOKD({ onLogout }: DashboardOKDProps) {
  const data = useDashboardData()

  return (
    <div className="dashboard-okd-container">
      <Sidebar
        user={{ username: data.username, avatarLetter: data.avatarLetter }}
        activeView={data.activeView}
        onNavigate={data.setActiveView}
        fileStatus={{
          mortalidad: {
            hasFile: Boolean(data.mortalidadFile),
            hasError: Boolean(data.mortalidadError),
          },
          morbilidad: {
            hasFile: Boolean(data.morbilidadFile),
            hasError: Boolean(data.morbilidadError),
          },
        }}
        onLogout={onLogout}
      />

      <main className="main-content-okd">
        <div className="content-area-okd">
          <ViewRouter
            activeView={data.activeView}
            data={data}
            onNavigate={data.setActiveView}
          />
        </div>
      </main>
    </div>
  )
}
