# Filtros de Período — Regras de Negócio

## Objetivo

Padronizar os filtros de período utilizados nas abas de Dashboard (gastos) e Histórico de Preços (produtos), garantindo consistência visual e funcional.

## Regras

### Regra 1: Opções de período

| Opção | Descrição | Cálculo |
|-------|-----------|---------|
| 1 semana | Últimos 7 dias | hoje - 7 dias |
| 1 mês | Últimos 30 dias | hoje - 30 dias |
| 3 meses | Último trimestre | hoje - 90 dias |
| 6 meses | Último semestre | hoje - 180 dias |
| 1 ano | Últimos 12 meses | hoje - 365 dias |
| 3 anos | Período máximo | hoje - 1095 dias |

### Regra 2: Período máximo

O sistema retorna no máximo **3 anos** de dados históricos. Registros anteriores a 3 anos não são exibidos nos gráficos e tabelas.

### Regra 3: Filtro padrão

O filtro padrão ao abrir qualquer aba é **3 meses** (90 dias).

### Regra 4: Filtro por mercado (Dashboard)

No Dashboard, o gráfico de gastos permite:
- **Todos**: linha única com soma de todas as notas
- **Por mercado**: uma linha por emitente (mercado) onde o usuário comprou

### Regra 5: Reutilização de componente

O componente de filtro de período é compartilhado entre Dashboard e Histórico de Preços para garantir:
- Mesma aparência visual
- Mesmas opções disponíveis
- Comportamento consistente

### Regra 6: Formato de data

Todas as datas exibidas no sistema seguem o formato **DD/MM/YYYY** (padrão brasileiro).

## Componente compartilhado

Localização: `frontend/src/components/PeriodFilter.jsx`

Props:
- `periodo` — valor atual selecionado (em dias)
- `onChange` — callback quando o período muda
- `showMercadoFilter` — boolean, exibe filtro por mercado (apenas Dashboard)
- `mercadoMode` — 'todos' | 'por_mercado'
- `onMercadoChange` — callback quando modo mercado muda
