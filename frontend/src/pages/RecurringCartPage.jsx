import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import './RecurringCartPage.css'

function RecurringCartPage() {
  const { api } = useAuth()
  const [carrinho, setCarrinho] = useState([])
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(true)
  const [sortBy, setSortBy] = useState('num_notas')

  useEffect(() => {
    const fetchCart = async () => {
      try {
        const res = await api.get('/me/carrinho-recorrente')
        setCarrinho(res.data.carrinho || [])
        setMessage(res.data.message || '')
      } catch (err) {
        console.error('Erro ao buscar carrinho:', err)
      } finally {
        setLoading(false)
      }
    }
    fetchCart()
  }, [api])

  const sorted = [...carrinho].sort((a, b) => {
    if (sortBy === 'num_notas') return b.num_notas - a.num_notas
    if (sortBy === 'descricao') return a.descricao.localeCompare(b.descricao)
    if (sortBy === 'preco_medio') return a.preco_medio - b.preco_medio
    return 0
  })

  return (
    <div className="cart-page">
      <header className="cart-header">
        <div>
          <h1>🛒 Carrinho Recorrente</h1>
          <p className="cart-subtitle">Produtos que você compra com frequência</p>
        </div>
        <Link to="/dashboard" className="cart-back">← Voltar</Link>
      </header>

      {loading && <p className="cart-loading">Carregando...</p>}

      {!loading && message && (
        <div className="cart-message">{message}</div>
      )}

      {!loading && carrinho.length > 0 && (
        <>
          <div className="cart-sort">
            <span>Ordenar por:</span>
            <button className={sortBy === 'num_notas' ? 'active' : ''} onClick={() => setSortBy('num_notas')}>Frequência</button>
            <button className={sortBy === 'descricao' ? 'active' : ''} onClick={() => setSortBy('descricao')}>Nome</button>
            <button className={sortBy === 'preco_medio' ? 'active' : ''} onClick={() => setSortBy('preco_medio')}>Preço</button>
          </div>

          <div className="cart-list">
            {sorted.map((item, i) => (
              <div key={i} className="cart-item">
                <div className="cart-item-info">
                  <span className="cart-item-name">{item.descricao}</span>
                  <span className="cart-item-meta">
                    {item.ean && <span className="cart-ean">EAN: {item.ean}</span>}
                    <span className="cart-freq">Em {item.num_notas} nota{item.num_notas > 1 ? 's' : ''}</span>
                    <span className="cart-qty">Qtd total: {item.quantidade_total}</span>
                  </span>
                </div>
                <span className="cart-item-price">
                  R$ {item.preco_medio.toFixed(2).replace('.', ',')}
                  <small>/un médio</small>
                </span>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  )
}

export default RecurringCartPage
