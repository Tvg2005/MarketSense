import { useState, useEffect } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { Package, ChevronDown, ChevronUp, Trash2 } from 'lucide-react'
import './Pages.css'

function ProdutosPage() {
  const { api } = useAuth()
  const [produtos, setProdutos] = useState([])
  const [loading, setLoading] = useState(true)
  const [sortBy, setSortBy] = useState('descricao')
  const [expandedKey, setExpandedKey] = useState(null)
  const [detalhes, setDetalhes] = useState(null)
  const [loadingDetalhe, setLoadingDetalhe] = useState(false)

  useEffect(() => {
    fetchProdutos()
  }, [api])

  const fetchProdutos = async () => {
    try {
      const res = await api.get('/me/produtos')
      setProdutos(res.data.produtos || [])
    } catch (err) { console.error(err) }
    finally { setLoading(false) }
  }

  const toggleDetalhe = async (groupKey) => {
    if (expandedKey === groupKey) {
      setExpandedKey(null)
      setDetalhes(null)
      return
    }
    setExpandedKey(groupKey)
    setLoadingDetalhe(true)
    try {
      const res = await api.get(`/me/produtos/${encodeURIComponent(groupKey)}/detalhes`)
      setDetalhes(res.data)
    } catch (err) { console.error(err) }
    finally { setLoadingDetalhe(false) }
  }

  const removerProduto = async (produtoId) => {
    if (!window.confirm('Remover este registro do produto?')) return
    try {
      await api.delete(`/me/produtos/${produtoId}`)
      // Atualiza detalhes removendo o item
      if (detalhes) {
        const novasOcorrencias = detalhes.ocorrencias.filter(o => o.produto_id !== produtoId)
        if (novasOcorrencias.length === 0) {
          setExpandedKey(null)
          setDetalhes(null)
          fetchProdutos()
        } else {
          setDetalhes({ ...detalhes, ocorrencias: novasOcorrencias })
        }
      }
    } catch (err) { console.error(err) }
  }

  const sorted = [...produtos].sort((a, b) => {
    if (sortBy === 'descricao') return a.descricao.localeCompare(b.descricao)
    if (sortBy === 'preco_medio') return b.preco_medio - a.preco_medio
    if (sortBy === 'num_notas') return b.num_notas - a.num_notas
    return 0
  })

  return (
    <div className="page">
      <h1 className="page-title">Produtos</h1>
      <p className="page-subtitle">Todos os produtos das suas notas fiscais</p>

      <div className="sort-bar">
        <span>Ordenar:</span>
        {[['descricao', 'Nome'], ['num_notas', 'Frequência'], ['preco_medio', 'Preço']].map(([key, label]) => (
          <button key={key} className={`sort-btn ${sortBy === key ? 'active' : ''}`} onClick={() => setSortBy(key)}>{label}</button>
        ))}
      </div>

      {loading ? <p className="muted">Carregando...</p> : sorted.length === 0 ? (
        <div className="empty-state">
          <Package size={40} className="wip-icon-svg" />
          <p>Nenhum produto encontrado. Extraia uma nota fiscal para começar.</p>
        </div>
      ) : (
        <div className="list">
          {sorted.map((p) => (
            <div key={p.group_key} className="list-item-wrapper">
              <div className="list-item" onClick={() => toggleDetalhe(p.group_key)}>
                <div className="li-left">
                  <span className="li-title">{p.descricao}</span>
                  <span className="li-sub">
                    {p.ean ? `EAN: ${p.ean}` : 'Sem EAN'} — Em {p.num_notas} nota{p.num_notas > 1 ? 's' : ''}
                  </span>
                </div>
                <div className="li-right">
                  <span className="li-value">R$ {p.preco_medio.toFixed(2).replace('.', ',')}</span>
                  <span className="li-sub-right">média/un</span>
                  {expandedKey === p.group_key ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                </div>
              </div>

              {expandedKey === p.group_key && (
                <div className="detail-panel">
                  {loadingDetalhe ? (
                    <p className="muted">Carregando detalhes...</p>
                  ) : detalhes ? (
                    <>
                      <div className="detail-section">
                        <h4>Ocorrências em notas ({detalhes.ocorrencias.length})</h4>
                        <div className="produtos-detail-list">
                          {detalhes.ocorrencias.map((oc) => (
                            <div key={oc.produto_id} className="produto-detail-row">
                              <div className="pd-info">
                                <span className="pd-nome">{oc.emitente}</span>
                                <span className="pd-sub">
                                  {oc.data_emissao ? new Date(oc.data_emissao).toLocaleDateString('pt-BR') : '-'}
                                </span>
                              </div>
                              <span className="pd-qtd">{oc.quantidade} {oc.unidade}</span>
                              <span className="pd-preco-unit">R$ {oc.valor_unitario?.toFixed(2).replace('.', ',')}/un</span>
                              <span className="pd-preco">R$ {oc.valor_total?.toFixed(2).replace('.', ',')}</span>
                              <button
                                className="btn-icon delete"
                                onClick={(e) => { e.stopPropagation(); removerProduto(oc.produto_id) }}
                                title="Remover este registro"
                              >
                                <Trash2 size={14} />
                              </button>
                            </div>
                          ))}
                        </div>
                      </div>
                    </>
                  ) : null}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default ProdutosPage
