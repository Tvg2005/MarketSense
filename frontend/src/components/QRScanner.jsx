import { useState, useRef, useCallback } from 'react'
import { BrowserQRCodeReader } from '@zxing/library'
import './QRScanner.css'

function QRScanner({ onDetected, onFallbackManual, disabled }) {
  const [status, setStatus] = useState(null) // null | 'processing' | 'success' | 'error'
  const [statusMsg, setStatusMsg] = useState('')
  const [preview, setPreview] = useState(null)
  const [showFallback, setShowFallback] = useState(false)
  const fileInputRef = useRef(null)

  const extrairChave = (texto) => {
    // Tenta extrair de URL com parâmetro Chave
    const matchUrl = texto.match(/[Cc]have=(\d{44})/)
    if (matchUrl) return matchUrl[1]

    // Tenta pegar 44 dígitos consecutivos
    const digits = texto.replace(/\D/g, '')
    if (digits.length >= 44) return digits.substring(0, 44)

    return null
  }

  const tentarZXing = async (file) => {
    return new Promise((resolve) => {
      const reader = new FileReader()
      reader.onload = () => {
        const img = new Image()
        img.onload = () => {
          // Tentar em múltiplas resoluções para melhorar detecção
          const tentativas = [
            { w: img.width, h: img.height },
            { w: img.width * 2, h: img.height * 2 },
            { w: Math.min(img.width, 1000), h: Math.min(img.height, 1000) },
          ]

          let encontrado = false
          for (const { w, h } of tentativas) {
            if (encontrado) break
            try {
              const canvas = document.createElement('canvas')
              canvas.width = w
              canvas.height = h
              const ctx = canvas.getContext('2d')

              // Fundo branco para melhorar contraste
              ctx.fillStyle = '#ffffff'
              ctx.fillRect(0, 0, w, h)
              ctx.drawImage(img, 0, 0, w, h)

              // Binarização manual para melhorar leitura
              const imageData = ctx.getImageData(0, 0, w, h)
              const data = imageData.data
              for (let i = 0; i < data.length; i += 4) {
                const gray = data[i] * 0.299 + data[i + 1] * 0.587 + data[i + 2] * 0.114
                const bin = gray > 128 ? 255 : 0
                data[i] = bin
                data[i + 1] = bin
                data[i + 2] = bin
              }
              ctx.putImageData(imageData, 0, 0)

              const codeReader = new BrowserQRCodeReader()
              const luminance = codeReader.createLuminanceSource(canvas)
              if (luminance) {
                // ZXing via canvas element
              }
            } catch (e) {
              // continua tentando
            }
          }

          // Abordagem direta com BrowserQRCodeReader.decodeFromImageElement
          try {
            const codeReader = new BrowserQRCodeReader()
            const imgEl = document.createElement('img')
            imgEl.src = reader.result
            imgEl.onload = async () => {
              try {
                const result = await codeReader.decodeFromImageElement(imgEl)
                resolve(result ? result.getText() : null)
              } catch (e) {
                resolve(null)
              }
            }
            imgEl.onerror = () => resolve(null)
          } catch (e) {
            resolve(null)
          }
        }
        img.onerror = () => resolve(null)
        img.src = reader.result
      }
      reader.onerror = () => resolve(null)
      reader.readAsDataURL(file)
    })
  }

  const tentarBackend = async (file) => {
    const formData = new FormData()
    formData.append('imagem', file)

    try {
      const resp = await fetch('/decodificar-qr', { method: 'POST', body: formData })
      const data = await resp.json()
      if (data.sucesso) return data.chave
    } catch (e) {
      console.log('Backend QR decode falhou:', e)
    }
    return null
  }

  const processarImagem = useCallback(async (file) => {
    if (file.size > 5 * 1024 * 1024) {
      setStatus('error')
      setStatusMsg('Arquivo muito grande. Máximo 5MB.')
      return
    }

    setPreview(URL.createObjectURL(file))
    setShowFallback(false)
    setStatus('processing')
    setStatusMsg('Decodificando QR Code...')

    // Tentativa 1: ZXing no browser
    const resultadoZXing = await tentarZXing(file)
    if (resultadoZXing) {
      const chave = extrairChave(resultadoZXing)
      if (chave) {
        setStatus('success')
        setStatusMsg(`Chave detectada: ${chave.slice(0, 8)}...${chave.slice(-8)}`)
        onDetected(chave)
        return
      }
    }

    // Tentativa 2: Backend com OpenCV + pyzbar
    setStatusMsg('Processando com análise avançada...')
    const resultadoBackend = await tentarBackend(file)
    if (resultadoBackend) {
      setStatus('success')
      setStatusMsg(`Chave detectada: ${resultadoBackend.slice(0, 8)}...${resultadoBackend.slice(-8)}`)
      onDetected(resultadoBackend)
      return
    }

    // Fallback: mostrar opções
    setStatus('error')
    setStatusMsg('Não foi possível ler o QR Code da imagem.')
    setShowFallback(true)
  }, [onDetected])

  const handleDrop = useCallback((e) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.dataTransfer.files.length > 0) {
      processarImagem(e.dataTransfer.files[0])
    }
  }, [processarImagem])

  const handleDragOver = (e) => {
    e.preventDefault()
    e.stopPropagation()
  }

  return (
    <div className="qr-scanner">
      <div
        className="upload-zone"
        onClick={() => fileInputRef.current?.click()}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
      >
        <div className="upload-icon">📷</div>
        <div className="upload-text">Clique ou arraste uma imagem do QR Code</div>
        <div className="upload-hint">PNG, JPG ou JPEG — máx. 5MB</div>
      </div>

      <input
        ref={fileInputRef}
        type="file"
        accept="image/png,image/jpeg,image/jpg"
        style={{ display: 'none' }}
        onChange={(e) => e.target.files[0] && processarImagem(e.target.files[0])}
      />

      {preview && (
        <div className="preview-area">
          <img src={preview} alt="Preview do QR Code" />
        </div>
      )}

      {status && (
        <div className={`qr-status ${status}`}>
          {status === 'processing' && <span className="spinner" />}
          {statusMsg}
        </div>
      )}

      {showFallback && (
        <div className="fallback-box">
          <p>Não foi possível ler automaticamente. Tente:</p>
          <div className="fallback-actions">
            <button className="btn-ghost" onClick={() => fileInputRef.current?.click()}>
              📷 Enviar outra foto
            </button>
            <button className="btn-ghost" onClick={onFallbackManual}>
              ⌨️ Digitar a chave
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

export default QRScanner
