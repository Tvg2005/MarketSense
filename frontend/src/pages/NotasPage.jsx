import { useState, useEffect } from 'react'
import { useAuth } from '../contexts/AuthContext'
import './Pages.css'

function NotasPage() {
  const { api } = useAuth()
  const [notas, setNotas] = useState([])
  const [loading, setLoading] = useState(true)
  const [detalhes, setDetalhes] = useState(null)

  useEffect(() => {
    fetchNotas()
  }, [api])

  const fetchNotas = async () => {
    try {
      const res = await api.get('/me/notas')
      setNotas(res.data.notas)
    } catch (err) { console.error(err) }
    finally { setLoading(false) }
  }

  const verDetalhes = async (chave) => {
    if (detalhes?.nota?.chave_acesso === chave) { setDetalhes(null); return }
    try {
      const res = await api.get(`/me/notas/${chave}`)
      setDetalhes(res.data)
    } catch (err) { console.error(err) }
  }

  const excluir = async (chave) => {
    if (!window.confirm('Remover esta nota do seu histórico?')) return
    try {
      await api.delete(`/me/notas/${chave}`)
      setNotas(notas.filter(n => n.chave_acesso !== chave))
      if (detalhes?.nota?.chave_acesso === chave) setDetalhes(null)
    } catch (err) { console.error(err) }
  }

  return (
    <div className="page">
      <h1 className="page-title">Notas Fiscais</h1>
      {loading ? <p className="muted">Carregando...</p> : notas.length === 0 ? (
        <div className="empty-state">
          <p>Nenhuma nota fiscal registrada.</p>
        </div>
      ) : (
        <div className="list">
          {notas.map(nota => (
            <div key={nota.chave_acesso} className="list-item-wrapper">
              <div className="list-item" onClick={() => verDetalhes(nota.chave_acesso)}>
                <div className="li-left">
                  <span className="li-title">{nota.emitente}</span>
                  <span className="li-sub">{nota.data_emissao ? new Date(nota.data_emissao).toLocaleDateString('pt-BR') : '-'}</span>
                </div>
                <div className="li-right">
                  <span className="li-value">R$ {nota.valor_total?.toFixed(2).replace('.', ',')}</span>
                  <button className="btn-icon delete" onClick={(e) => { e.stopPropagation(); excluir(nota.chave_acesso) }} title="Excluir">✕</button>
                </div>
              </div>
              {detalhes?.nota?.chave_acesso === nota.chave_acesso && (
                <div className="detail-panel">
                  <div className="detail-grid">
                    <div className="detail-section">
                      <h4>Emitente</h4>
                      <p>{detalhes.nota.emitente.razao_social}</p>
                      <p className="muted">{detalhes.nota.emitente.cnpj} — {detalhes.nota.emitente.endereco}, {detalhes.nota.emitente.bairro}</p>
                    </div>
                    <div className="detail-section">
                      <h4>Nota</h4>
                      <p>Nº {detalhes.nota.numero} | Série {detalhes.nota.serie} | {detalhes.nota.natureza_operacao}</p>
                      <p className="muted small">Chave: {detalhes.nota.chave_acesso}</p>
                    </div>
                  </div>
                  <div className="detail-section">
                    <h4>Produtos ({detalhes.nota.produtos.length})</h4>
                    <div className="produtos-detail-list">
                      {detalhes.nota.produtos.map((p, i) => (
                        <div key={i} className="produto-detail-row">
                          <span className="pd-nome">{p.descricao}</span>
                          <span className="pd-qtd">{p.quantidade} {p.unidade}</span>
                          <span className="pd-preco">R$ {p.valor_total?.toFixed(2).replace('.', ',')}</span>
                        </div>
                      ))}
                    </div>
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

export default NotasPage
