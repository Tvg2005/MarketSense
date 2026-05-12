import './ResultPanel.css'

function ResultPanel({ resultado }) {
  if (!resultado) return null

  const { produtos, metadados } = resultado

  return (
    <div className="result-panel">
      <h2>Produtos Extraídos ({produtos?.length || 0})</h2>

      {produtos && produtos.length > 0 && (
        <div className="produtos-list">
          {produtos.map((p, i) => (
            <div key={i} className="produto-row">
              <div className="produto-info">
                <span className="produto-nome">{p.nome}</span>
                <span className="produto-codigo">#{p.codigo}</span>
              </div>
              <span className="produto-preco">{p.preco_formatado}</span>
            </div>
          ))}
        </div>
      )}

      {metadados?.Emitente && (
        <div className="meta-section">
          <h3>Emitente</h3>
          <div className="meta-grid">
            {Object.entries(metadados.Emitente)
              .filter(([, v]) => v && v.trim())
              .map(([key, value]) => (
                <div key={key} className="meta-cell">
                  <span className="meta-label">{key}</span>
                  <span className="meta-value">{value}</span>
                </div>
              ))}
          </div>
        </div>
      )}

      {metadados?.Totais && (
        <div className="meta-section">
          <h3>Totais</h3>
          <div className="meta-grid">
            {Object.entries(metadados.Totais)
              .filter(([, v]) => v && v.trim())
              .map(([key, value]) => (
                <div key={key} className="meta-cell">
                  <span className="meta-label">{key}</span>
                  <span className="meta-value">{value}</span>
                </div>
              ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default ResultPanel
