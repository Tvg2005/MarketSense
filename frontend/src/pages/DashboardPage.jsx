import { useState, useEffect } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { FileText, Package, DollarSign, MapPin } from 'lucide-react'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend } from 'recharts'
import PeriodFilter from '../components/PeriodFilter.jsx'
import './DashboardPage.css'

const COLORS = ['#14B8A6', '#3B82F6', '#8B5CF6', '#EC4899', '#F97316', '#22C55E', '#EAB308']

function DashboardPage() {
  const { api } = useAuth()
  const [stats, setStats] = useState({ notas: 0, produtos: 0 })
  const [carrinho, setCarrinho] = useState([])
  const [gastos, setGastos] = useState([])
  const [loading, setLoading] = useState(true)
  const [periodo, setPeriodo] = useState(90)
  const [mercadoMode, setMercadoMode] = useState('todos')

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const [notasRes, carrinhoRes] = await Promise.all([
          api.get('/me/notas'),
          api.get('/me/carrinho-recorrente'),
        ])
        setStats({ notas: (notasRes.data.notas || []).length, produtos: (carrinhoRes.data.carrinho || []).length })
        setCarrinho((carrinhoRes.data.carrinho || []).slice(0, 5))
      } catch (err) { console.error(err) }
      finally { setLoading(false) }
    }
    fetchStats()
  }, [api])

  useEffect(() => {
    const fetchGastos = async () => {
      try {
        const res = await api.get(`/me/gastos?dias=${periodo}`)
        setGastos(res.data.gastos || [])
      } catch (err) { console.error(err) }
    }
    fetchGastos()
  }, [api, periodo])

  const formatDate = (iso) => {
    if (!iso) return '-'
    return new Date(iso).toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric' })
  }

  // Prepara dados do gráfico
  const chartData = (() => {
    if (mercadoMode === 'todos') {
      return gastos.map(g => ({ data: formatDate(g.data), valor: g.valor }))
    }
    // Por mercado: pivot
    const mercados = [...new Set(gastos.map(g => g.mercado))]
    const byDate = {}
    gastos.forEach(g => {
      const d = formatDate(g.data)
      if (!byDate[d]) byDate[d] = { data: d }
      byDate[d][g.mercado] = (byDate[d][g.mercado] || 0) + g.valor
    })
    return { data: Object.values(byDate), mercados }
  })()

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

      {/* Gráfico de gastos */}
      <div className="dash-section">
        <h2>Histórico de Gastos</h2>
        <PeriodFilter
          periodo={periodo}
          onChange={setPeriodo}
          showMercadoFilter={true}
          mercadoMode={mercadoMode}
          onMercadoChange={setMercadoMode}
        />
        {gastos.length === 0 ? (
          <p className="empty-text">Sem dados de gastos para o período selecionado.</p>
        ) : (
          <div className="gastos-chart">
            <ResponsiveContainer width="100%" height={280}>
              <LineChart data={mercadoMode === 'todos' ? chartData : chartData.data}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                <XAxis dataKey="data" tick={{ fontSize: 11, fill: 'var(--text-muted)' }} />
                <YAxis tick={{ fontSize: 11, fill: 'var(--text-muted)' }} tickFormatter={(v) => `R$${v.toFixed(0)}`} />
                <Tooltip
                  contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 8 }}
                  formatter={(value) => [`R$ ${Number(value).toFixed(2).replace('.', ',')}`, '']}
                />
                {mercadoMode === 'todos' ? (
                  <Line type="monotone" dataKey="valor" stroke="var(--color-primary)" strokeWidth={2} dot={{ r: 4 }} name="Total" />
                ) : (
                  chartData.mercados?.map((mercado, i) => (
                    <Line key={mercado} type="monotone" dataKey={mercado} stroke={COLORS[i % COLORS.length]} strokeWidth={2} dot={{ r: 3 }} name={mercado} />
                  ))
                )}
                {mercadoMode === 'por_mercado' && <Legend wrapperStyle={{ fontSize: '0.75rem' }} />}
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
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
