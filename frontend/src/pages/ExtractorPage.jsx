import { useState, useEffect, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { io } from 'socket.io-client'
import { useAuth } from '../contexts/AuthContext'
import QRScanner from '../components/QRScanner.jsx'
import StatusPanel from '../components/StatusPanel.jsx'
import ResultPanel from '../components/ResultPanel.jsx'
import './ExtractorPage.css'

const socket = io('/', { transports: ['websocket', 'polling'] })

function ExtractorPage() {
  const { token } = useAuth()
  const [tab, setTab] = useState('manual')
  const [chave, setChave] = useState('')
  const [extraindo, setExtraindo] = useState(false)
  const [statusList, setStatusList] = useState([])
  const [resultado, setResultado] = useState(null)

  useEffect(() => {
    socket.on('status_update', (data) => {
      setStatusList(prev => [...prev, data])
    })

    socket.on('extracao_finalizada', (data) => {
      setExtraindo(false)
      if (data.sucesso) {
        setResultado({ produtos: data.produtos, metadados: data.metadados })
      }
    })

    return () => {
      socket.off('status_update')
      socket.off('extracao_finalizada')
    }
  }, [])

  const iniciarExtracao = useCallback((chaveInput) => {
    const valor = chaveInput || chave
    if (!valor.trim()) return

    setExtraindo(true)
    setStatusList([])
    setResultado(null)
    socket.emit('iniciar_extracao', { chave: valor.trim(), token })
  }, [chave, token])

  const onQRDetected = useCallback((chaveDetectada) => {
    setChave(chaveDetectada)
    setTab('manual')
    setExtraindo(true)
    setStatusList([])
    setResultado(null)
    socket.emit('iniciar_extracao', { chave: chaveDetectada, token })
  }, [token])

  return (
    <div className="extractor-page">
      <header className="ext-header">
        <h1>Extrair Nota Fiscal</h1>
        <Link to="/dashboard" className="ext-back">← Voltar</Link>
      </header>

      <div className="tabs">
        <button className={`tab ${tab === 'manual' ? 'active' : ''}`} onClick={() => setTab('manual')}>
          ⌨️ Chave de Acesso
        </button>
        <button className={`tab ${tab === 'qrcode' ? 'active' : ''}`} onClick={() => setTab('qrcode')}>
          📷 QR Code
        </button>
      </div>

      {tab === 'manual' && (
        <div className="manual-input">
          <div className="input-row">
            <input
              type="text"
              value={chave}
              onChange={(e) => setChave(e.target.value.replace(/\D/g, '').slice(0, 44))}
              placeholder="Digite os 44 dígitos da chave de acesso"
              maxLength={44}
              onKeyDown={(e) => e.key === 'Enter' && iniciarExtracao()}
              disabled={extraindo}
            />
            <button
              className="btn-primary"
              onClick={() => iniciarExtracao()}
              disabled={extraindo || chave.length < 44}
            >
              {extraindo ? 'Extraindo...' : 'Extrair'}
            </button>
          </div>
          <div className="chave-counter">{chave.length}/44 dígitos</div>
        </div>
      )}

      {tab === 'qrcode' && (
        <QRScanner
          onDetected={onQRDetected}
          onFallbackManual={() => setTab('manual')}
          disabled={extraindo}
        />
      )}

      <StatusPanel statusList={statusList} visible={statusList.length > 0} />
      <ResultPanel resultado={resultado} />
    </div>
  )
}

export default ExtractorPage
