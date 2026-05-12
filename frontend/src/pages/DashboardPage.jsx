import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import './DashboardPage.css'

function DashboardPage() {
  const { user, logout, api } = useAuth()
  const [notas, setNotas] = useState([])
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    const fetchNotas = async () => {
      try {
        const res = await api.get('/me/notas')
        setNotas(res.data.notas)
      } catch (err) {
        console.error('Erro ao buscar notas:', err)
      } finally {
        setLoading(false)
      }
    }
    fetchNotas()
  }, [api])

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <div className="dashboard">
      <header className="dash-header">
        <div>
          <h1>NFE Analyser</h1>
          <p className="dash-email">{user?.email}</p>
        </div>
        <div className="dash-actions">
          <Link to="/extrair" className="dash-btn">+ Extrair Nota</Link>
          <Link to="/carrinho-recorrente" className="dash-btn secondary">🛒 Carrinho</Link>
          <button onClick={handleLogout} className="dash-btn logout">Sair</button>
        </div>
      </header>

      <section className="dash-content">
        <h2>Minhas Notas Fiscais ({notas.length})</h2>

        {loading && <p className="dash-loading">Carregando...</p>}

        {!loading && notas.length === 0 && (
          <div className="dash-empty">
            <p>Nenhuma nota fiscal encontrada.</p>
            <Link to="/extrair" className="dash-btn">Extrair sua primeira nota</Link>
          </div>
        )}

        {!loading && notas.length > 0 && (
          <div className="notas-list">
            {notas.map((nota) => (
              <div key={nota.chave_acesso} className="nota-card">
                <div className="nota-info">
                  <span className="nota-emitente">{nota.emitente}</span>
                  <span className="nota-data">
                    {nota.data_emissao ? new Date(nota.data_emissao).toLocaleDateString('pt-BR') : '-'}
                  </span>
                </div>
                <span className="nota-valor">
                  R$ {nota.valor_total?.toFixed(2).replace('.', ',')}
                </span>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  )
}

export default DashboardPage
