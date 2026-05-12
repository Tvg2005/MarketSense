import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './contexts/AuthContext.jsx'
import { ThemeProvider } from './contexts/ThemeContext.jsx'
import ProtectedRoute from './components/ProtectedRoute.jsx'
import AppLayout from './components/AppLayout.jsx'
import LoginPage from './pages/LoginPage.jsx'
import SignupPage from './pages/SignupPage.jsx'
import DashboardPage from './pages/DashboardPage.jsx'
import NotasPage from './pages/NotasPage.jsx'
import ProdutosPage from './pages/ProdutosPage.jsx'
import CarrinhoPage from './pages/CarrinhoPage.jsx'
import ExtractorPage from './pages/ExtractorPage.jsx'
import MercadosPage from './pages/MercadosPage.jsx'
import HistoricoPage from './pages/HistoricoPage.jsx'
import ConfigPage from './pages/ConfigPage.jsx'

function AppRoutes() {
  const { isAuthenticated } = useAuth()

  return (
    <Routes>
      <Route path="/login" element={isAuthenticated ? <Navigate to="/dashboard" /> : <LoginPage />} />
      <Route path="/signup" element={isAuthenticated ? <Navigate to="/dashboard" /> : <SignupPage />} />
      <Route path="/" element={<ProtectedRoute><AppLayout /></ProtectedRoute>}>
        <Route index element={<Navigate to="/dashboard" />} />
        <Route path="dashboard" element={<DashboardPage />} />
        <Route path="notas" element={<NotasPage />} />
        <Route path="produtos" element={<ProdutosPage />} />
        <Route path="carrinho" element={<CarrinhoPage />} />
        <Route path="extrair" element={<ExtractorPage />} />
        <Route path="mercados" element={<MercadosPage />} />
        <Route path="historico" element={<HistoricoPage />} />
        <Route path="configuracoes" element={<ConfigPage />} />
      </Route>
      <Route path="*" element={<Navigate to={isAuthenticated ? "/dashboard" : "/login"} />} />
    </Routes>
  )
}

function App() {
  return (
    <BrowserRouter>
      <ThemeProvider>
        <AuthProvider>
          <AppRoutes />
        </AuthProvider>
      </ThemeProvider>
    </BrowserRouter>
  )
}

export default App
