# Histórico de Preços — Regras de Negócio

## Objetivo

Permitir que o usuário visualize a evolução dos preços dos produtos ao longo do tempo, comparando valores entre diferentes mercados.

## Regras

### Regra 1: Escopo dos dados

O histórico de preços é **coletivo** — utiliza dados de TODAS as notas fiscais do sistema, não apenas as do usuário logado. Isso garante uma base de dados mais rica para comparação.

### Regra 2: Mínimo de registros

Um produto só aparece no histórico de preços se tiver **pelo menos 2 registros** em qualquer nota do sistema (independente do usuário). Produtos com apenas 1 registro não têm histórico suficiente para exibir tendência.

### Regra 3: Agrupamento via Catálogo Interno

O agrupamento de produtos usa o `catalogo_id` da tabela `catalogo_produtos`:
- Produtos com EAN válido são agrupados pelo EAN (via catálogo)
- Produtos sem EAN são vinculados ao catálogo pela regra de similaridade léxica (≥85%) + NCM
- Isso permite que o mesmo produto vendido em mercados diferentes (com ou sem EAN) tenha histórico unificado

### Regra 4: Dados exibidos por produto

Para cada produto no histórico:
- **Gráfico de linha**: evolução do preço unitário ao longo do tempo
- **Preço atual**: último preço registrado
- **Preço mínimo/máximo**: no período disponível
- **Variação**: percentual de mudança entre primeiro e último registro
- **Mercados**: quais emitentes vendem o produto e a que preço

### Regra 5: Filtros disponíveis

- Por produto (busca por nome/EAN)
- Por período (últimos 30, 60, 90 dias ou personalizado)
- Por mercado (filtrar por emitente específico)

### Regra 6: Visibilidade

O usuário só vê no histórico os produtos que **ele próprio comprou** (presentes nas suas notas via `users_notas`), mas os dados de preço incluem registros de outros usuários para o mesmo produto (via `catalogo_id`).

## Modelo de Dados

A query principal usa:
```sql
SELECT 
    cp.id as catalogo_id,
    cp.descricao_canonica,
    cp.ean,
    p.valor_unitario,
    p.unidade,
    n.data_emissao,
    e.nome_fantasia as mercado
FROM produtos p
JOIN catalogo_produtos cp ON cp.id = p.catalogo_id
JOIN notas n ON n.chave_acesso = p.nota_chave
JOIN emitentes e ON e.cnpj = n.emitente_cnpj
WHERE cp.id IN (
    -- Produtos do usuário
    SELECT DISTINCT p2.catalogo_id 
    FROM produtos p2
    JOIN users_notas un ON un.nota_chave = p2.nota_chave
    WHERE un.user_id = :user_id
)
AND cp.id IN (
    -- Apenas produtos com 2+ registros no sistema
    SELECT catalogo_id FROM produtos 
    GROUP BY catalogo_id HAVING COUNT(*) >= 2
)
ORDER BY n.data_emissao;
```
