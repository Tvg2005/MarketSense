import { NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext.jsx'
import { useTheme } from '../contexts/ThemeContext.jsx'
import {
  LayoutDashboard, FileText, Package, ShoppingCart,
  MapPin, TrendingUp, Settings, PlusCircle, LogOut
} from 'lucide-react'
import './Sidebar.css'

const navItems = [
  { path: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { path: '/notas', icon: FileText, label: 'Notas Fiscais' },
  { path: '/produtos', icon: Package, label: 'Produtos' },
  { path: '/carrinho', icon: ShoppingCart, label: 'Carrinho' },
  { path: '/mercados', icon: MapPin, label: 'Melhores Mercados' },
  { path: '/historico', icon: TrendingUp, label: 'Histórico de Preços' },
]

function Sidebar() {
  const { user, logout } = useAuth()
  const { theme, toggleTheme } = useTheme()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <img src="/logo.png" alt="MarketSense" className="sidebar-logo" />
        <span className="sidebar-brand">Market<b>Sense</b></span>
      </div>

      <nav className="sidebar-nav">
        {navItems.map(item => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
          >
            <item.icon size={20} className="nav-icon-svg" />
            <span className="nav-label">{item.label}</span>
          </NavLink>
        ))}
      </nav>

      <div className="sidebar-bottom">
        <NavLink to="/configuracoes" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
          <Settings size={20} className="nav-icon-svg" />
          <span className="nav-label">Configurações</span>
        </NavLink>

        <NavLink to="/extrair" className="nav-item extract-btn">
          <PlusCircle size={20} className="nav-icon-svg" />
          <span className="nav-label">Extrair Nota</span>
        </NavLink>

        <div className="sidebar-user">
          <div className="user-info">
            <div className="user-avatar">{user?.email?.[0]?.toUpperCase()}</div>
            <span className="user-email">{user?.email}</span>
          </div>
          <button className="btn-logout" onClick={handleLogout} title="Sair da conta">
            <LogOut size={16} />
          </button>
        </div>
      </div>
    </aside>
  )
}

export default Sidebar
