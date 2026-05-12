import { CheckCircle, AlertCircle, Info, XCircle } from 'lucide-react'
import './StatusPanel.css'

const ICONS = {
  info: Info,
  success: CheckCircle,
  warning: AlertCircle,
  error: XCircle,
}

function StatusPanel({ statusList, visible }) {
  if (!visible) return null

  return (
    <div className="status-panel">
      <h2>Progresso</h2>
      <div className="status-list">
        {statusList.map((item, i) => {
          const Icon = ICONS[item.tipo] || Info
          return (
            <div key={i} className={`status-item ${item.tipo}`}>
              <Icon size={16} className="status-icon" />
              <span>{item.mensagem}</span>
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default StatusPanel
