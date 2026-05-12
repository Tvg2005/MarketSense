import './PeriodFilter.css'

const PERIODOS = [
  { label: '1 sem', value: 7 },
  { label: '1 mês', value: 30 },
  { label: '3 meses', value: 90 },
  { label: '6 meses', value: 180 },
  { label: '1 ano', value: 365 },
  { label: '3 anos', value: 1095 },
]

function PeriodFilter({ periodo, onChange, showMercadoFilter, mercadoMode, onMercadoChange }) {
  return (
    <div className="period-filter">
      <div className="pf-group">
        <span className="pf-label">Período:</span>
        <div className="pf-buttons">
          {PERIODOS.map(p => (
            <button
              key={p.value}
              className={`pf-btn ${periodo === p.value ? 'active' : ''}`}
              onClick={() => onChange(p.value)}
            >
              {p.label}
            </button>
          ))}
        </div>
      </div>

      {showMercadoFilter && (
        <div className="pf-group">
          <span className="pf-label">Visualizar:</span>
          <div className="pf-buttons">
            <button className={`pf-btn ${mercadoMode === 'todos' ? 'active' : ''}`} onClick={() => onMercadoChange('todos')}>
              Todos
            </button>
            <button className={`pf-btn ${mercadoMode === 'por_mercado' ? 'active' : ''}`} onClick={() => onMercadoChange('por_mercado')}>
              Por mercado
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

export default PeriodFilter
