import { TrendingUp } from 'lucide-react'
import './Pages.css'

function HistoricoPage() {
  return (
    <div className="page">
      <h1 className="page-title">Histórico de Preços</h1>
      <div className="wip-state">
        <TrendingUp size={48} className="wip-icon-svg" />
        <h2>Em desenvolvimento</h2>
        <p>Em breve você poderá acompanhar a evolução dos preços dos seus produtos ao longo do tempo, com gráficos comparativos entre mercados.</p>
      </div>
    </div>
  )
}

export default HistoricoPage
