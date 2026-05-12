import './StatusPanel.css'

function StatusPanel({ statusList, visible }) {
  if (!visible) return null

  return (
    <div className="status-panel">
      <h2>Status da Extração</h2>
      <div className="status-list">
        {statusList.map((item, i) => (
          <div key={i} className={`status-item ${item.tipo}`}>
            {item.mensagem}
          </div>
        ))}
      </div>
    </div>
  )
}

export default StatusPanel
