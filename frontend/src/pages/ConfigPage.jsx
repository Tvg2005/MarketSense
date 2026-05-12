import { useTheme } from '../contexts/ThemeContext'
import './Pages.css'
import './ConfigPage.css'

const ACCENT_COLORS = [
  { name: 'Verde Teal', value: '#14B8A6' },
  { name: 'Azul', value: '#3B82F6' },
  { name: 'Roxo', value: '#8B5CF6' },
  { name: 'Rosa', value: '#EC4899' },
  { name: 'Laranja', value: '#F97316' },
  { name: 'Amarelo', value: '#EAB308' },
  { name: 'Verde', value: '#22C55E' },
  { name: 'Vermelho', value: '#EF4444' },
]

function ConfigPage() {
  const { theme, toggleTheme, accentColor, setAccentColor } = useTheme()

  return (
    <div className="page">
      <h1 className="page-title">Configurações</h1>

      <div className="config-section">
        <h2>Aparência</h2>

        <div className="config-item">
          <div className="config-label">
            <span>Tema</span>
            <span className="config-desc">Alterne entre modo claro e escuro</span>
          </div>
          <button className="theme-toggle" onClick={toggleTheme}>
            {theme === 'dark' ? '🌙 Escuro' : '☀️ Claro'}
          </button>
        </div>

        <div className="config-item">
          <div className="config-label">
            <span>Cor de destaque</span>
            <span className="config-desc">Personalize a cor principal da interface</span>
          </div>
          <div className="color-grid">
            {ACCENT_COLORS.map(c => (
              <button
                key={c.value}
                className={`color-swatch ${accentColor === c.value ? 'active' : ''}`}
                style={{ background: c.value }}
                onClick={() => setAccentColor(c.value)}
                title={c.name}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

export default ConfigPage
