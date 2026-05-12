import { useState, useEffect } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { FileText, Package, DollarSign, MapPin } from 'lucide-react'
import './DashboardPage.css'

function DashboardPage() {
  const { api } = useAuth()
  const [stats, setStats] = useState({ notas: 0, produtos: 0 })
  const [carrinho, setCarrinho] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [notasRes, carrinhoRes] = await Promise.all([
          api.get('/me/notas'),
          api.get('/me/carrinho-recorrente'),
        ])
        const notas = notasRes.data.notas || []
        const cart = carrinhoRes.data.carrinho || []
        setStats({ notas: notas.length, produtos: cart.length })
        setCarrinho(cart.slice(0, 5))
      } catch (err) { console.error(err) }
      finally { setLoading(false) }
    }
    fetchData()
  }, [api])

  return (
    <div className="dashboard-page">
      <h1 className="page-title">Resumo</h1>
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-header">
            <span className="stat-label">Notas Fiscais</span>
            <span className="stat-icon-wrap"><FileText size={22} /></span>
          </div>
          <span className="stat-value">{stats.notas}</span>
          <span className="stat-sub">Total registradas</span>
        </div>
        <div className="stat-card">
          <div className="stat-header">
            <span className="stat-label">Produtos Rastreados</span>
            <span className="stat-icon-wrap"><Package size={22} /></span>
          </div>
          <span className="stat-value">{stats.produtos}</span>
          <span className="stat-sub">Produtos únicos</span>
        </div>
        <div className="stat-card">
          <div className="stat-header">
            <span className="stat-label">Economia Potencial</span>
            <span className="stat-icon-wrap"><DollarSign size={22} /></span>
          </div>
          <span className="stat-value">Em breve</span>
          <span className="stat-sub">Com seu carrinho</span>
        </div>
        <div className="stat-card">
          <div className="stat-header">
            <span className="stat-label">Mercado Recomendado</span>
            <span className="stat-icon-wrap"><MapPin size={22} /></span>
          </div>
          <span className="stat-value">Em breve</span>
          <span className="stat-sub">Melhor custo-benefício</span>
        </div>
      </div>

      <div className="dashboard-grid">
        <div className="dash-section">
          <h2>Seu Carrinho <span className="section-sub">(produtos recorrentes)</span></h2>
          {loading ? (
            <p className="loading-text">Carregando...</p>
          ) : carrinho.length === 0 ? (
            <p className="empty-text">Extraia pelo menos 2 notas para gerar seu carrinho recorrente.</p>
          ) : (
            <table className="cart-table">
              <thead><tr><th>Produto</th><th>Qtd.</th><th>Preço médio</th></tr></thead>
              <tbody>
                {carrinho.map((item, i) => (
                  <tr key={i}>
                    <td className="td-produto">{item.descricao}</td>
                    <td className="td-qtd">{item.num_notas}</td>
                    <td className="td-preco">R$ {item.preco_medio.toFixed(2).replace('.', ',')}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
        <div className="dash-section side-section">
          <h2>Melhor mercado para você</h2>
          <div className="coming-soon">
            <MapPin size={40} className="cs-icon-svg" />
            <p>Em desenvolvimento</p>
            <small>Recomendações baseadas no seu carrinho estarão disponíveis em breve.</small>
          </div>
        </div>
      </div>
    </div>
  )
}

export default DashboardPage
