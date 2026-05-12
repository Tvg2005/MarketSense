# Catálogo Interno de Produtos — Regras de Negócio

## Objetivo

Criar uma chave interna unificada para todos os produtos do sistema, permitindo rastrear histórico de preços mesmo para produtos que não possuem EAN (código de barras) nas notas fiscais.

## Problema

Muitos produtos nas NFC-e vêm com o campo EAN marcado como "SEM GTIN" ou vazio. Isso impede o agrupamento correto para:
- Histórico de preços
- Carrinho recorrente
- Comparação entre mercados

## Solução: Tabela `catalogo_produtos`

Uma tabela centralizada que funciona como catálogo canônico de produtos. Cada produto no sistema recebe um `produto_canonical_id` que aponta para este catálogo.

### Estrutura

| Campo | Tipo | Descrição |
|-------|------|-----------|
| id | SERIAL PK | Chave interna do sistema |
| ean | VARCHAR(20) | EAN canônico (null se produto nunca teve EAN) |
| descricao_canonica | VARCHAR(255) | Descrição padronizada do produto |
| unidade | VARCHAR(10) | Unidade de medida (UN, KG, L, etc.) |
| ncm | VARCHAR(10) | Código NCM (quando disponível) |
| criado_em | TIMESTAMP | Data de criação do registro |
| atualizado_em | TIMESTAMP | Última atualização |

### Regras de Vinculação

#### Regra 1: Produto com EAN válido
- Se o produto tem EAN válido (não é "SEM GTIN", não é vazio, não é null):
  - Busca no catálogo por EAN exato
  - Se encontrar → vincula ao registro existente
  - Se não encontrar → cria novo registro no catálogo

#### Regra 2: Produto sem EAN — Matching por similaridade
- Se o produto NÃO tem EAN válido:
  1. Busca candidatos no catálogo com a **mesma unidade de medida**
  2. Para cada candidato, calcula a **similaridade léxica** entre as descrições
  3. Se a similaridade for **≥ 85%** → vincula ao registro existente
  4. Se nenhum candidato atingir 85% → cria novo registro no catálogo

#### Regra 3: Herança de EAN
- Se um produto sem EAN é vinculado a um registro do catálogo que JÁ possui EAN (vindo de outro produto com EAN):
  - O produto herda o EAN do catálogo para fins de histórico de preços
  - O EAN original do produto na nota permanece inalterado (preserva dado original)

### Algoritmo de Similaridade

- **Método**: SequenceMatcher do módulo `difflib` (Python stdlib)
- **Pré-processamento**:
  1. Converter para uppercase
  2. Remover acentos (normalize NFKD)
  3. Remover caracteres especiais (manter apenas alfanuméricos e espaços)
  4. Normalizar espaços múltiplos
- **Threshold dinâmico com NCM**:
  - Ambos têm NCM e são **iguais** → threshold **75%** (NCM confirma categoria, mais permissivo)
  - Ambos têm NCM e são **diferentes** → **rejeita match** (independente da similaridade textual)
  - Um ou ambos **sem NCM** → threshold padrão **85%**
- **Critérios obrigatórios para comparação**:
  - Mesma unidade de medida (case-insensitive)

### Regra do NCM como Boost de Confiança

O NCM (Nomenclatura Comum do Mercosul) classifica produtos por categoria fiscal. Ele é usado como **fator de ajuste** no matching, não como filtro eliminatório isolado:

| NCM Produto A | NCM Produto B | Efeito no Matching |
|---------------|---------------|-------------------|
| Preenchido | Igual | Threshold reduzido para 75% (alta confiança) |
| Preenchido | Diferente | Match rejeitado (categorias incompatíveis) |
| Preenchido | Vazio/null | Threshold padrão 85% |
| Vazio/null | Vazio/null | Threshold padrão 85% |

**Justificativa**: Dois produtos com mesmo NCM + mesma unidade + descrição similar têm altíssima probabilidade de serem o mesmo item. Já NCMs diferentes indicam categorias fiscais distintas, o que invalida o match mesmo com descrições parecidas (ex: "LEITE INTEGRAL 1L" vs "LEITE CONDENSADO 1L").

### Performance

- Índice composto em `(unidade, descricao_canonica)` para busca rápida de candidatos
- Índice único em `ean` (quando não null) para lookup direto
- O matching por similaridade é executado apenas para produtos sem EAN (minoria dos casos)
- Cache em memória dos registros do catálogo durante o processamento de uma nota (evita N queries)

### Fluxo de Inserção

```
Produto chega da NFC-e
    │
    ├─ Tem EAN válido?
    │   ├─ SIM → Busca catálogo por EAN
    │   │       ├─ Encontrou → vincula (produto.catalogo_id = registro.id)
    │   │       └─ Não encontrou → cria registro no catálogo, vincula
    │   │
    │   └─ NÃO → Busca candidatos (mesma unidade)
    │           ├─ Algum com similaridade ≥ 85%?
    │           │   ├─ SIM → vincula ao melhor match
    │           │   └─ NÃO → cria registro no catálogo, vincula
    │
    └─ Salva produto com catalogo_id preenchido
```

### Impacto no Histórico de Preços

A tabela `precos_historico` passa a usar `catalogo_id` como chave de agrupamento em vez de `ean`. Isso permite:
- Produtos sem EAN terem histórico de preços
- Produtos com EAN diferentes mas que são o mesmo item (embalagens diferentes) serem unificados manualmente no futuro

### Considerações Futuras

- Interface para o usuário confirmar/rejeitar vinculações automáticas
- Merge manual de registros do catálogo pelo admin
- Integração com APIs de produtos (Open Food Facts, Cosmos) para enriquecer dados
