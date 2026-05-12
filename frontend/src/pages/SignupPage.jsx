import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { TERMOS_TEXTO } from '../constants/termos'
import './AuthPages.css'

function getPasswordStrength(password) {
  if (!password) return null
  let score = 0
  if (password.length >= 8) score++
  if (password.length >= 12) score++
  if (/[A-Z]/.test(password)) score++
  if (/[0-9]/.test(password)) score++
  if (/[^A-Za-z0-9]/.test(password)) score++

  if (score <= 2) return { level: 'weak', label: 'Fraca' }
  if (score <= 3) return { level: 'moderate', label: 'Moderada' }
  return { level: 'strong', label: 'Forte' }
}

function SignupPage() {
  const [form, setForm] = useState({
    nome: '', email: '', password: '', confirmPassword: '',
    cep: '', endereco: '', numero: '', complemento: '', bairro: '', cidade: '', uf: ''
  })
  const [termsAccepted, setTermsAccepted] = useState(false)
  const [termsRead, setTermsRead] = useState(false)
  const [showTerms, setShowTerms] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const { signup } = useAuth()
  const navigate = useNavigate()

  const updateField = (field, value) => setForm(prev => ({ ...prev, [field]: value }))

  const handleTermsScroll = (e) => {
    const { scrollTop, scrollHeight, clientHeight } = e.target
    if (scrollTop + clientHeight >= scrollHeight - 20) setTermsRead(true)
  }

  const buscarCep = async (cep) => {
    const cepLimpo = cep.replace(/\D/g, '')
    if (cepLimpo.length !== 8) return
    try {
      const res = await fetch(`https://viacep.com.br/ws/${cepLimpo}/json/`)
      const data = await res.json()
      if (!data.erro) {
        setForm(prev => ({
          ...prev,
          endereco: data.logradouro || prev.endereco,
          bairro: data.bairro || prev.bairro,
          cidade: data.localidade || prev.cidade,
          uf: data.uf || prev.uf,
        }))
      }
    } catch (err) { /* silencioso */ }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')

    if (form.password !== form.confirmPassword) { setError('As senhas não coincidem'); return }
    if (form.password.length < 8) { setError('A senha deve ter pelo menos 8 caracteres'); return }
    if (!termsAccepted) { setError('Você precisa ler e aceitar os termos de uso'); return }

    setLoading(true)
    try {
      await signup(form.email, form.password, {
        nome: form.nome, cep: form.cep, endereco: form.endereco,
        numero: form.numero, complemento: form.complemento,
        bairro: form.bairro, cidade: form.cidade, uf: form.uf,
      })
      navigate('/dashboard')
    } catch (err) {
      setError(err.response?.data?.error || 'Erro ao criar conta')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-card auth-card-wide">
        <div className="auth-logo">
          <img src="/logo.png" alt="MarketSense" />
          <span>Market<b>Sense</b></span>
        </div>
        <p className="auth-subtitle">Crie sua conta</p>

        <form onSubmit={handleSubmit} className="auth-form">
          {error && <div className="auth-error">{error}</div>}

          <div className="form-group">
            <label>Nome completo</label>
            <input value={form.nome} onChange={(e) => updateField('nome', e.target.value)} placeholder="Seu nome" required disabled={loading} />
          </div>

          <div className="form-group">
            <label>Email</label>
            <input type="email" value={form.email} onChange={(e) => updateField('email', e.target.value)} placeholder="seu@email.com" required disabled={loading} />
          </div>

          <div className="form-row">
            <div className="form-group form-grow">
              <label>Senha</label>
              <input type="password" value={form.password} onChange={(e) => updateField('password', e.target.value)} placeholder="Mínimo 8 caracteres" required disabled={loading} />
              {form.password && (() => {
                const strength = getPasswordStrength(form.password)
                return (
                  <div className="password-strength">
                    <div className="strength-bar"><div className={`strength-fill ${strength.level}`} /></div>
                    <span className={`strength-label ${strength.level}`}>Senha {strength.label}</span>
                  </div>
                )
              })()}
            </div>
            <div className="form-group form-grow">
              <label>Confirmar senha</label>
              <input type="password" value={form.confirmPassword} onChange={(e) => updateField('confirmPassword', e.target.value)} placeholder="Repita a senha" required disabled={loading} />
            </div>
          </div>

          <div className="form-divider">Endereço</div>

          <div className="form-row">
            <div className="form-group form-sm">
              <label>CEP</label>
              <input value={form.cep} onChange={(e) => { const v = e.target.value.replace(/\D/g, '').slice(0, 8); updateField('cep', v); if (v.length === 8) buscarCep(v) }} placeholder="00000000" disabled={loading} />
            </div>
            <div className="form-group form-grow">
              <label>Endereço</label>
              <input value={form.endereco} onChange={(e) => updateField('endereco', e.target.value)} placeholder="Rua, Avenida..." disabled={loading} />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group form-sm">
              <label>Número</label>
              <input value={form.numero} onChange={(e) => updateField('numero', e.target.value)} placeholder="Nº" disabled={loading} />
            </div>
            <div className="form-group form-grow">
              <label>Complemento</label>
              <input value={form.complemento} onChange={(e) => updateField('complemento', e.target.value)} placeholder="Apto, Bloco..." disabled={loading} />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group form-grow">
              <label>Bairro</label>
              <input value={form.bairro} onChange={(e) => updateField('bairro', e.target.value)} placeholder="Bairro" disabled={loading} />
            </div>
            <div className="form-group form-grow">
              <label>Cidade</label>
              <input value={form.cidade} onChange={(e) => updateField('cidade', e.target.value)} placeholder="Cidade" disabled={loading} />
            </div>
            <div className="form-group form-xs">
              <label>UF</label>
              <input value={form.uf} onChange={(e) => updateField('uf', e.target.value.toUpperCase().slice(0, 2))} placeholder="DF" maxLength={2} disabled={loading} />
            </div>
          </div>

          <div className="terms-section">
            {showTerms && (
              <>
                <div className="terms-box" onScroll={handleTermsScroll}>
                  <pre className="terms-text">{TERMOS_TEXTO}</pre>
                </div>
                <button type="button" className="terms-toggle" onClick={() => setShowTerms(false)}>
                  📄 Ocultar Termos de Uso e Consentimento
                </button>
              </>
            )}
            <label className="terms-checkbox">
              <input type="checkbox" checked={termsAccepted} onChange={(e) => setTermsAccepted(e.target.checked)} disabled={!termsRead && !termsAccepted} />
              <span>Li e aceito os <button type="button" className="terms-link" onClick={() => setShowTerms(true)}>Termos de Uso e Consentimento</button></span>
            </label>
            {!termsRead && !termsAccepted && <p className="terms-hint">Leia os termos até o final para habilitar o aceite</p>}
          </div>

          <button type="submit" className="auth-btn" disabled={loading || !termsAccepted}>
            {loading ? 'Criando...' : 'Criar conta'}
          </button>
        </form>

        <p className="auth-link">Já tem conta? <Link to="/login">Entrar</Link></p>
      </div>
    </div>
  )
}

export default SignupPage
