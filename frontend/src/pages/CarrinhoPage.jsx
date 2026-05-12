import { useState, useEffect } from 'react'
import { useAuth } from '../contexts/AuthContext'
import './Pages.css'

function CarrinhoPage() {
  const { api } = useAuth()
  const [carrinho, setCarrinho] = useState([])
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetch = async () => {
      try {
        const res = await api.get('/me/carrinho-recorrente')
        setCarrinho(res.data.carrinho || [])
        setMessage(res.data.message || '')
      } catch (err) { console.error(err) }
      finally { setLoading(false) }
    }
    fetch()
  }, [api])

  const totalEstimado = carrinho.reduce((acc, item) => acc + item.preco_medio, 0)

  return (
    <div className="page">
      <h1 className="page-title">Carrinho Recorrente</h1>
      <p className="page-subtitle">Produtos que você compra com frequência</p>

      {loading ? <p className="muted">Carregando...</p> : message ? (
        <div className="info-box">{message}</div>
      ) : (
        <>
          <table className="data-table">
            <thead>
              <tr>
                <th>Produto</th>
                <th>Qtd.</th>
                <th>Preço médio</th>
              </tr>
            </thead>
            <tbody>
              {carrinho.map((item, i) => (
                <tr key={i}>
                  <td>
                    <span className="td-main">{item.descricao}</span>
                    {item.ean && <span className="td-sub">EAN: {item.ean}</span>}
                  </td>
                  <td className="td-center">{item.num_notas}</td>
                  <td className="td-accent">R$ {item.preco_medio.toFixed(2).replace('.', ',')}</td>
                </tr>
              ))}
            </tbody>
            <tfoot>
              <tr>
                <td colSpan="2" className="td-total-label">Total estimado</td>
                <td className="td-total-value">R$ {totalEstimado.toFixed(2).replace('.', ',')}</td>
              </tr>
            </tfoot>
          </table>
        </>
      )}
    </div>
  )
}

export default CarrinhoPage
