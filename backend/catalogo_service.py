"""Serviço de catálogo interno de produtos.

Responsável por vincular produtos das NFC-e ao catálogo canônico,
usando EAN direto ou matching por similaridade léxica + NCM.
"""

from difflib import SequenceMatcher
from unicodedata import normalize, category
from models import SessionLocal, CatalogoProduto, Produto


def _normalizar_texto(texto):
    """Normaliza texto para comparação: uppercase, sem acentos, sem especiais."""
    if not texto:
        return ""
    # Uppercase
    texto = texto.upper()
    # Remove acentos (NFKD decompose + remove combining chars)
    texto = ''.join(
        c for c in normalize('NFKD', texto)
        if category(c) != 'Mn'
    )
    # Remove caracteres não alfanuméricos (mantém espaços)
    texto = ''.join(c if c.isalnum() or c == ' ' else ' ' for c in texto)
    # Normaliza espaços múltiplos
    texto = ' '.join(texto.split())
    return texto


def _calcular_similaridade(desc_a, desc_b):
    """Calcula similaridade entre duas descrições normalizadas."""
    a = _normalizar_texto(desc_a)
    b = _normalizar_texto(desc_b)
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()


def _ean_valido(ean):
    """Verifica se o EAN é válido (não é SEM GTIN, vazio ou null)."""
    if not ean:
        return False
    ean = ean.strip()
    return ean != '' and ean.upper() != 'SEM GTIN'


def _determinar_threshold(ncm_produto, ncm_candidato):
    """
    Determina o threshold de similaridade com base no NCM.
    - Ambos preenchidos e iguais → 75% (alta confiança)
    - Ambos preenchidos e diferentes → rejeita (retorna None)
    - Um ou ambos vazios → 85% (padrão)
    """
    tem_ncm_produto = bool(ncm_produto and ncm_produto.strip())
    tem_ncm_candidato = bool(ncm_candidato and ncm_candidato.strip())

    if tem_ncm_produto and tem_ncm_candidato:
        if ncm_produto.strip() == ncm_candidato.strip():
            return 0.75  # NCM confirma categoria, mais permissivo
        else:
            return None  # Categorias incompatíveis, rejeita
    return 0.85  # Padrão quando NCM ausente


def vincular_ao_catalogo(session, ean, descricao, unidade, ncm):
    """
    Vincula um produto ao catálogo canônico.
    Retorna o catalogo_id correspondente.
    """
    # Caso 1: Produto com EAN válido
    if _ean_valido(ean):
        catalogo = session.query(CatalogoProduto).filter_by(ean=ean).first()
        if catalogo:
            # Atualiza NCM se estava vazio
            if ncm and not catalogo.ncm:
                catalogo.ncm = ncm
            return catalogo.id

        # Cria novo registro no catálogo
        catalogo = CatalogoProduto(
            ean=ean,
            descricao_canonica=descricao or '',
            unidade=(unidade or '').upper(),
            ncm=ncm,
        )
        session.add(catalogo)
        session.flush()  # Gera o ID sem commitar
        return catalogo.id

    # Caso 2: Produto sem EAN — matching por similaridade
    unidade_norm = (unidade or '').upper().strip()

    # Busca candidatos com mesma unidade
    candidatos = (
        session.query(CatalogoProduto)
        .filter(CatalogoProduto.unidade == unidade_norm)
        .all()
    )

    melhor_match = None
    melhor_score = 0.0

    for candidato in candidatos:
        # Determina threshold com base no NCM
        threshold = _determinar_threshold(ncm, candidato.ncm)
        if threshold is None:
            continue  # NCMs diferentes, rejeita

        score = _calcular_similaridade(descricao, candidato.descricao_canonica)
        if score >= threshold and score > melhor_score:
            melhor_score = score
            melhor_match = candidato

    if melhor_match:
        return melhor_match.id

    # Caso 3: Nenhum match — cria novo registro
    catalogo = CatalogoProduto(
        ean=None,
        descricao_canonica=descricao or '',
        unidade=unidade_norm,
        ncm=ncm,
    )
    session.add(catalogo)
    session.flush()
    return catalogo.id
