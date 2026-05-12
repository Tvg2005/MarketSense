import { MapPin } from 'lucide-react'
import './Pages.css'

function MercadosPage() {
  return (
    <div className="page">
      <h1 className="page-title">Melhores Mercados</h1>
      <div className="wip-state">
        <MapPin size={48} className="wip-icon-svg" />
        <h2>Em desenvolvimento</h2>
        <p>Em breve você poderá ver recomendações de mercados com base nos preços dos produtos do seu carrinho recorrente e na sua localização.</p>
      </div>
    </div>
  )
}

export default MercadosPage
