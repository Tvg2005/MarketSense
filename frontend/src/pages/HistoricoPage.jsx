import { useState, useEffect } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { TrendingUp, TrendingDown, Minus, Search } from 'lucide-react'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts'
import './Pages.css'
import './HistoricoPage.css'

function HistoricoPage() {
  const { api } = useAuth()
  const [historico, setHistorico] = useState([])
  const [loading, setLoading] = useState(true)
  const [busca, setBusca] = useState('')
  const [expandedId, setExpandedId] = useState(null)

  useEffect(() => {
    const fetch = async () => {
      try {
        const res = await api.get('/me/historico-precos')
        setHistorico(res.data.historico || [])
      } catch (err) { console.error(err) }
      finally { setLoading(false) }
    }
    fetch()
  }, [api])

  const filtrado = historico.filter(p =>
    p.descricao.toLowerCase().includes(busca.toLowerCase()) ||
    (p.ean && p.ean.includes(busca))
  )

  const formatDate = (iso) => {
    if (!iso) return '-'
    return new Date(iso).toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' })
  }

  return (
    <div className="page">
      <h1 className="page-title">Histórico de Preços</h1>
      <p className="page-subtitle">Evolução dos preços dos seus produtos ao longo do tempo</p>

      <div className="search-bar">
        <Search size={16} className="search-icon" />
        <input
          type="text"
          value={busca}
          onChange={(e) => setBusca(e.target.value)}
          placeholder="Buscar por produto ou EAN..."
        />
      </div>

      {loading ? <p className="muted">Carregando...</p> : filtrado.length === 0 ? (
        <div className="empty-state">
          <TrendingUp size={40} className="wip-icon-svg" />
          <p>{busca ? 'Nenhum produto encontrado para essa busca.' : 'Nenhum produto com histórico de preços disponível. Extraia mais notas para gerar dados.'}</p>
        </div>
      ) : (
        <div className="historico-list">
          {filtrado.map((prod) => (
            <div key={prod.catalogo_id} className="historico-card">
              <div className="hc-header" onClick={() => setExpandedId(expandedId === prod.catalogo_id ? null : prod.catalogo_id)}>
                <div className="hc-info">
                  <span className="hc-nome">{prod.descricao}</span>
                  <span className="hc-meta">
                    {prod.ean && <span className="hc-ean">EAN: {prod.ean}</span>}
                    <span className="hc-regs">{prod.num_registros} registros</span>
                    <span className="hc-mercados">{prod.mercados.length} mercado{prod.mercados.length > 1 ? 's' : ''}</span>
                  </span>
                </div>
                <div className="hc-stats">
                  <span className="hc-preco">R$ {prod.preco_atual.toFixed(2).replace('.', ',')}</span>
                  <span className={`hc-variacao ${prod.variacao_pct > 0 ? 'up' : prod.variacao_pct < 0 ? 'down' : 'neutral'}`}>
                    {prod.variacao_pct > 0 ? <TrendingUp size={14} /> : prod.variacao_pct < 0 ? <TrendingDown size={14} /> : <Minus size={14} />}
                    {prod.variacao_pct > 0 ? '+' : ''}{prod.variacao_pct}%
                  </span>
                </div>
              </div>

              {expandedId === prod.catalogo_id && (
                <div className="hc-detail">
                  <div className="hc-metrics">
                    <div className="hc-metric">
                      <span className="hcm-label">Mínimo</span>
                      <span className="hcm-value green">R$ {prod.preco_min.toFixed(2).replace('.', ',')}</span>
                    </div>
                    <div className="hc-metric">
                      <span className="hcm-label">Máximo</span>
                      <span className="hcm-value red">R$ {prod.preco_max.toFixed(2).replace('.', ',')}</span>
                    </div>
                    <div className="hc-metric">
                      <span className="hcm-label">Atual</span>
                      <span className="hcm-value">R$ {prod.preco_atual.toFixed(2).replace('.', ',')}</span>
                    </div>
                    <div className="hc-metric">
                      <span className="hcm-label">Mercados</span>
                      <span className="hcm-value">{prod.mercados.join(', ')}</span>
                    </div>
                  </div>

                  <div className="hc-chart">
                    <ResponsiveContainer width="100%" height={200}>
                      <LineChart data={prod.registros.map(r => ({ ...r, dataLabel: formatDate(r.data) }))}>
                        <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                        <XAxis dataKey="dataLabel" tick={{ fontSize: 11, fill: 'var(--text-muted)' }} />
                        <YAxis tick={{ fontSize: 11, fill: 'var(--text-muted)' }} tickFormatter={(v) => `R$${v.toFixed(0)}`} />
                        <Tooltip
                          contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 8 }}
                          labelStyle={{ color: 'var(--text-secondary)' }}
                          formatter={(value, name) => [`R$ ${value.toFixed(2).replace('.', ',')}`, 'Preço']}
                          labelFormatter={(label) => label}
                        />
                        <Line type="monotone" dataKey="valor" stroke="var(--color-primary)" strokeWidth={2} dot={{ r: 4, fill: 'var(--color-primary)' }} />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>

                  <div className="hc-table">
                    <table className="data-table">
                      <thead><tr><th>Data</th><th>Mercado</th><th>Preço</th></tr></thead>
                      <tbody>
                        {prod.registros.map((r, i) => (
                          <tr key={i}>
                            <td>{formatDate(r.data)}</td>
                            <td>{r.mercado}</td>
                            <td className="td-accent">R$ {r.valor.toFixed(2).replace('.', ',')}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default HistoricoPage
