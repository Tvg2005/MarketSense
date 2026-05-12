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


@me_bp.route('/notas/<chave_acesso>', methods=['GET'])
@token_required
def get_nota_detalhe(current_user_id, chave_acesso):
    """Retorna os detalhes completos de uma nota fiscal."""
    session = SessionLocal()
    try:
        nota = (
            session.query(Nota)
            .join(UserNota, UserNota.nota_chave == Nota.chave_acesso)
            .filter(UserNota.user_id == int(current_user_id))
            .filter(Nota.chave_acesso == chave_acesso)
            .first()
        )

        if not nota:
            return jsonify({"error": "Nota não encontrada"}), 404

        produtos = []
        for p in nota.produtos:
            produtos.append({
                "ean": p.ean,
                "codigo_produto": p.codigo_produto,
                "descricao": p.descricao,
                "quantidade": p.quantidade,
                "unidade": p.unidade,
                "valor_unitario": p.valor_unitario,
                "valor_total": p.valor_total,
                "ncm": p.ncm,
                "cfop": p.cfop,
            })

        emitente = {}
        if nota.emitente:
            emitente = {
                "cnpj": nota.emitente.cnpj,
                "razao_social": nota.emitente.razao_social,
                "nome_fantasia": nota.emitente.nome_fantasia,
                "endereco": nota.emitente.endereco,
                "bairro": nota.emitente.bairro,
                "cep": nota.emitente.cep,
                "municipio": nota.emitente.municipio,
                "uf": nota.emitente.uf,
            }

        return jsonify({
            "nota": {
                "chave_acesso": nota.chave_acesso,
                "numero": nota.numero,
                "serie": nota.serie,
                "data_emissao": nota.data_emissao.isoformat() if nota.data_emissao else None,
                "valor_total": nota.valor_total,
                "natureza_operacao": nota.natureza_operacao,
                "emitente": emitente,
                "produtos": produtos,
            }
        }), 200
    finally:
        session.close()


@me_bp.route('/notas/<chave_acesso>', methods=['DELETE'])
@token_required
def delete_nota(current_user_id, chave_acesso):
    """Remove a associação da nota com o usuário (não deleta a nota do banco)."""
    session = SessionLocal()
    try:
        user_nota = (
            session.query(UserNota)
            .filter(UserNota.user_id == int(current_user_id))
            .filter(UserNota.nota_chave == chave_acesso)
            .first()
        )

        if not user_nota:
            return jsonify({"error": "Nota não encontrada"}), 404

        session.delete(user_nota)
        session.commit()
        return jsonify({"message": "Nota removida com sucesso"}), 200
    except Exception as e:
        session.rollback()
        return jsonify({"error": "Erro ao remover nota"}), 500
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


@me_bp.route('/produtos', methods=['GET'])
@token_required
def get_produtos(current_user_id):
    """Lista todos os produtos do usuário agrupados por EAN/descrição."""
    session = SessionLocal()
    try:
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
            .order_by(func.max(Produto.descricao))
            .all()
        )

        produtos = []
        for row in results:
            produtos.append({
                "group_key": row.group_key,
                "ean": row.ean,
                "descricao": row.descricao,
                "quantidade_total": round(row.quantidade_total, 2) if row.quantidade_total else 0,
                "num_notas": row.num_notas,
                "preco_medio": round(row.preco_medio, 2) if row.preco_medio else 0,
            })

        return jsonify({"produtos": produtos}), 200
    finally:
        session.close()


@me_bp.route('/produtos/<path:group_key>/detalhes', methods=['GET'])
@token_required
def get_produto_detalhes(current_user_id, group_key):
    """Retorna detalhes de um produto em cada nota onde aparece."""
    session = SessionLocal()
    try:
        # Busca todas as ocorrências desse produto nas notas do usuário
        query = (
            session.query(Produto, Nota)
            .join(Nota, Nota.chave_acesso == Produto.nota_chave)
            .join(UserNota, UserNota.nota_chave == Produto.nota_chave)
            .filter(UserNota.user_id == int(current_user_id))
        )

        # Filtra por EAN ou descrição
        query = query.filter(
            (Produto.ean == group_key) | (Produto.descricao == group_key)
        )

        results = query.order_by(Nota.data_emissao.desc()).all()

        if not results:
            return jsonify({"error": "Produto não encontrado"}), 404

        ocorrencias = []
        for produto, nota in results:
            ocorrencias.append({
                "nota_chave": nota.chave_acesso,
                "emitente": nota.emitente.nome_fantasia or nota.emitente.razao_social if nota.emitente else "",
                "data_emissao": nota.data_emissao.isoformat() if nota.data_emissao else None,
                "quantidade": produto.quantidade,
                "unidade": produto.unidade,
                "valor_unitario": produto.valor_unitario,
                "valor_total": produto.valor_total,
                "produto_id": produto.id,
            })

        return jsonify({
            "descricao": results[0][0].descricao,
            "ean": results[0][0].ean,
            "ocorrencias": ocorrencias,
        }), 200
    finally:
        session.close()


@me_bp.route('/produtos/<int:produto_id>', methods=['DELETE'])
@token_required
def delete_produto(current_user_id, produto_id):
    """Remove um produto específico de uma nota do usuário."""
    session = SessionLocal()
    try:
        produto = (
            session.query(Produto)
            .join(UserNota, UserNota.nota_chave == Produto.nota_chave)
            .filter(UserNota.user_id == int(current_user_id))
            .filter(Produto.id == produto_id)
            .first()
        )

        if not produto:
            return jsonify({"error": "Produto não encontrado"}), 404

        session.delete(produto)
        session.commit()
        return jsonify({"message": "Produto removido"}), 200
    except Exception:
        session.rollback()
        return jsonify({"error": "Erro ao remover produto"}), 500
    finally:
        session.close()


@me_bp.route('/historico-precos', methods=['GET'])
@token_required
def get_historico_precos(current_user_id):
    """Retorna histórico de preços dos produtos do usuário (dados coletivos)."""
    session = SessionLocal()
    try:
        from models import CatalogoProduto, Emitente
        from sqlalchemy import and_

        # Produtos do usuário (via catalogo_id)
        user_catalogo_ids = (
            session.query(Produto.catalogo_id)
            .join(UserNota, UserNota.nota_chave == Produto.nota_chave)
            .filter(UserNota.user_id == int(current_user_id))
            .filter(Produto.catalogo_id.isnot(None))
            .distinct()
            .subquery()
        )

        # Apenas produtos com 2+ registros no sistema
        catalogo_com_historico = (
            session.query(Produto.catalogo_id)
            .filter(Produto.catalogo_id.isnot(None))
            .group_by(Produto.catalogo_id)
            .having(func.count(Produto.id) >= 2)
            .subquery()
        )

        # Query principal: todos os registros de preço para esses produtos
        results = (
            session.query(
                CatalogoProduto.id.label('catalogo_id'),
                CatalogoProduto.descricao_canonica,
                CatalogoProduto.ean,
                CatalogoProduto.unidade,
                Produto.valor_unitario,
                Nota.data_emissao,
                Emitente.nome_fantasia,
                Emitente.razao_social,
            )
            .join(Produto, Produto.catalogo_id == CatalogoProduto.id)
            .join(Nota, Nota.chave_acesso == Produto.nota_chave)
            .join(Emitente, Emitente.cnpj == Nota.emitente_cnpj)
            .filter(CatalogoProduto.id.in_(user_catalogo_ids))
            .filter(CatalogoProduto.id.in_(catalogo_com_historico))
            .order_by(CatalogoProduto.descricao_canonica, Nota.data_emissao)
            .all()
        )

        # Agrupa por produto
        produtos_historico = {}
        for row in results:
            cid = row.catalogo_id
            if cid not in produtos_historico:
                produtos_historico[cid] = {
                    "catalogo_id": cid,
                    "descricao": row.descricao_canonica,
                    "ean": row.ean,
                    "unidade": row.unidade,
                    "registros": [],
                }
            mercado = row.nome_fantasia or row.razao_social or ""
            produtos_historico[cid]["registros"].append({
                "data": row.data_emissao.isoformat() if row.data_emissao else None,
                "valor": round(row.valor_unitario, 2) if row.valor_unitario else 0,
                "mercado": mercado,
            })

        # Calcula métricas por produto
        historico = []
        for prod in produtos_historico.values():
            regs = prod["registros"]
            valores = [r["valor"] for r in regs if r["valor"] > 0]
            if not valores:
                continue

            preco_min = min(valores)
            preco_max = max(valores)
            preco_atual = valores[-1]
            preco_primeiro = valores[0]
            variacao = round(((preco_atual - preco_primeiro) / preco_primeiro) * 100, 1) if preco_primeiro > 0 else 0

            mercados = list(set(r["mercado"] for r in regs if r["mercado"]))

            historico.append({
                "catalogo_id": prod["catalogo_id"],
                "descricao": prod["descricao"],
                "ean": prod["ean"],
                "unidade": prod["unidade"],
                "preco_atual": preco_atual,
                "preco_min": preco_min,
                "preco_max": preco_max,
                "variacao_pct": variacao,
                "num_registros": len(regs),
                "mercados": mercados,
                "registros": regs,
            })

        historico.sort(key=lambda x: x["num_registros"], reverse=True)

        return jsonify({"historico": historico}), 200
    finally:
        session.close()


@me_bp.route('/gastos', methods=['GET'])
@token_required
def get_gastos(current_user_id):
    """Retorna histórico de gastos do usuário por nota fiscal."""
    from flask import request as flask_request
    from models import Emitente
    from datetime import timedelta

    dias = int(flask_request.args.get('dias', 90))
    dias = min(dias, 1095)  # Máximo 3 anos

    session = SessionLocal()
    try:
        from datetime import datetime
        data_inicio = datetime.utcnow() - timedelta(days=dias)

        results = (
            session.query(
                Nota.data_emissao,
                Nota.valor_total,
                Emitente.nome_fantasia,
                Emitente.razao_social,
            )
            .join(UserNota, UserNota.nota_chave == Nota.chave_acesso)
            .join(Emitente, Emitente.cnpj == Nota.emitente_cnpj)
            .filter(UserNota.user_id == int(current_user_id))
            .filter(Nota.data_emissao >= data_inicio)
            .order_by(Nota.data_emissao)
            .all()
        )

        gastos = []
        for row in results:
            mercado = row.nome_fantasia or row.razao_social or "Desconhecido"
            gastos.append({
                "data": row.data_emissao.isoformat() if row.data_emissao else None,
                "valor": round(row.valor_total, 2) if row.valor_total else 0,
                "mercado": mercado,
            })

        return jsonify({"gastos": gastos}), 200
    finally:
        session.close()
