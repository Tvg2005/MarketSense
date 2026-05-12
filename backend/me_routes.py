"""Blueprint de endpoints protegidos do usuário."""

from flask import Blueprint, jsonify
from auth_middleware import token_required
from models import SessionLocal, User, Nota, UserNota, Produto
from sqlalchemy import func, case, text

me_bp = Blueprint('me', __name__)


@me_bp.route('/notas', methods=['GET'])
@token_required
def get_notas(current_user_id):
    """Retorna as notas fiscais associadas ao usuário."""
    session = SessionLocal()
    try:
        notas = (
            session.query(Nota)
            .join(UserNota, UserNota.nota_chave == Nota.chave_acesso)
            .filter(UserNota.user_id == int(current_user_id))
            .all()
        )

        resultado = []
        for nota in notas:
            resultado.append({
                "chave_acesso": nota.chave_acesso,
                "emitente": nota.emitente.nome_fantasia or nota.emitente.razao_social if nota.emitente else "",
                "data_emissao": nota.data_emissao.isoformat() if nota.data_emissao else None,
                "valor_total": nota.valor_total,
            })

        return jsonify({"notas": resultado}), 200
    finally:
        session.close()


@me_bp.route('/carrinho-recorrente', methods=['GET'])
@token_required
def get_carrinho_recorrente(current_user_id):
    """Gera o carrinho recorrente baseado na frequência de compra do usuário."""
    session = SessionLocal()
    try:
        # Verifica se tem pelo menos 2 notas
        num_notas = (
            session.query(func.count(UserNota.nota_chave))
            .filter(UserNota.user_id == int(current_user_id))
            .scalar()
        )

        if num_notas < 2:
            return jsonify({
                "carrinho": [],
                "message": "Histórico insuficiente. Adicione pelo menos 2 notas fiscais."
            }), 200

        # Query de agregação por produto
        group_key = case(
            (Produto.ean.isnot(None) & (Produto.ean != 'SEM GTIN') & (Produto.ean != ''), Produto.ean),
            else_=Produto.descricao
        )

        results = (
            session.query(
                group_key.label('group_key'),
                func.max(Produto.descricao).label('descricao'),
                case(
                    (Produto.ean.isnot(None) & (Produto.ean != 'SEM GTIN') & (Produto.ean != ''), Produto.ean),
                    else_=None
                ).label('ean'),
                func.sum(Produto.quantidade).label('quantidade_total'),
                func.count(func.distinct(Produto.nota_chave)).label('num_notas'),
                func.avg(Produto.valor_unitario).label('preco_medio'),
            )
            .join(UserNota, UserNota.nota_chave == Produto.nota_chave)
            .filter(UserNota.user_id == int(current_user_id))
            .group_by('group_key', 'ean')
            .order_by(func.count(func.distinct(Produto.nota_chave)).desc(), func.sum(Produto.quantidade).desc())
            .all()
        )

        carrinho = []
        for row in results:
            carrinho.append({
                "ean": row.ean,
                "descricao": row.descricao,
                "quantidade_total": round(row.quantidade_total, 2) if row.quantidade_total else 0,
                "num_notas": row.num_notas,
                "preco_medio": round(row.preco_medio, 2) if row.preco_medio else 0,
            })

        return jsonify({"carrinho": carrinho}), 200
    finally:
        session.close()
