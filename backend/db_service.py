"""Serviço de persistência: salva os dados extraídos da NFC-e no PostgreSQL."""

from models import SessionLocal, Emitente, Nota, Produto, PrecoHistorico, UserNota
from catalogo_service import vincular_ao_catalogo
from datetime import datetime
import re
import json


def parse_data_emissao(data_str):
    """Converte string de data da SEFAZ para datetime."""
    if not data_str:
        return None
    # Formato: "03/05/2026 14:47:29-03:00"
    try:
        data_limpa = re.sub(r'[+-]\d{2}:\d{2}$', '', data_str.strip())
        return datetime.strptime(data_limpa, "%d/%m/%Y %H:%M:%S")
    except ValueError:
        try:
            return datetime.strptime(data_str.strip()[:10], "%d/%m/%Y")
        except ValueError:
            return None


def parse_float_br(valor_str):
    """
    Converte valor monetário BR (1.234,56) para float.
    Usado para valores como preço onde '.' é milhar e ',' é decimal.
    """
    if not valor_str:
        return 0.0
    try:
        return float(valor_str.replace('.', '').replace(',', '.'))
    except (ValueError, AttributeError):
        return 0.0


def parse_quantidade(valor_str):
    """
    Converte quantidade que usa '.' como decimal (ex: "1.0000", "4,0000").
    A SEFAZ usa tanto '.' quanto ',' como separador decimal em quantidades.
    """
    if not valor_str:
        return 0.0
    valor_str = valor_str.strip()
    try:
        # Se tem vírgula, é separador decimal BR
        if ',' in valor_str:
            return float(valor_str.replace('.', '').replace(',', '.'))
        # Se só tem ponto, é separador decimal padrão
        return float(valor_str)
    except (ValueError, AttributeError):
        return 0.0


def salvar_nota_completa(dados_json, user_id=None):
    """
    Recebe o dicionário completo extraído (nfe_metadados.json) e persiste no banco.
    Se user_id for fornecido, associa a nota ao usuário.
    Retorna a chave de acesso da nota salva.
    """
    session = SessionLocal()

    try:
        # 1. Emitente
        emitente_data = dados_json.get("Emitente", {})
        cnpj = emitente_data.get("CNPJ", "").strip()

        if not cnpj:
            raise ValueError("CNPJ do emitente não encontrado nos dados.")

        emitente = session.get(Emitente, cnpj)
        if not emitente:
            emitente = Emitente(
                cnpj=cnpj,
                razao_social=emitente_data.get("Nome / Razão Social", ""),
                nome_fantasia=emitente_data.get("Nome Fantasia", ""),
                endereco=emitente_data.get("Endereço", ""),
                bairro=emitente_data.get("Bairro / Distrito", ""),
                cep=emitente_data.get("CEP", ""),
                municipio=emitente_data.get("Município", ""),
                uf=emitente_data.get("UF", ""),
                inscricao_estadual=emitente_data.get("Inscrição Estadual", ""),
                regime_tributario=emitente_data.get("Regime Tributário", ""),
            )
            session.add(emitente)
        else:
            emitente.razao_social = emitente_data.get("Nome / Razão Social", "") or emitente.razao_social
            emitente.nome_fantasia = emitente_data.get("Nome Fantasia", "") or emitente.nome_fantasia

        # 2. Nota fiscal
        dados_gerais = dados_json.get("Dados Gerais", {})
        nfce_data = dados_json.get("NFC-e", {})
        totais_data = dados_json.get("Totais", {})

        chave_acesso = dados_gerais.get("Chave de acesso", "")
        chave_acesso = re.sub(r'\D', '', chave_acesso)

        if not chave_acesso or len(chave_acesso) != 44:
            raise ValueError(f"Chave de acesso inválida: {chave_acesso}")

        nota_existente = session.get(Nota, chave_acesso)
        if nota_existente:
            # Nota já existe, mas ainda precisa vincular ao usuário
            if user_id:
                existing_link = (
                    session.query(UserNota)
                    .filter_by(user_id=int(user_id), nota_chave=chave_acesso)
                    .first()
                )
                if not existing_link:
                    user_nota = UserNota(user_id=int(user_id), nota_chave=chave_acesso)
                    session.add(user_nota)
                    session.commit()
            session.close()
            return chave_acesso

        data_emissao = parse_data_emissao(nfce_data.get("Data de Emissão", ""))
        valor_total = parse_float_br(nfce_data.get("Valor Total da Nota Fiscal", ""))

        nota = Nota(
            chave_acesso=chave_acesso,
            emitente_cnpj=cnpj,
            numero=nfce_data.get("Número", ""),
            serie=nfce_data.get("Série", ""),
            data_emissao=data_emissao,
            valor_total=valor_total,
            natureza_operacao=nfce_data.get("Natureza da Operação", ""),
            dados_extras={
                "totais": totais_data,
                "destinatario": dados_json.get("Destinatário", {}),
                "transporte": dados_json.get("Transporte", {}),
                "cobranca": dados_json.get("Cobrança", {}),
                "inf_adic": dados_json.get("Inf Adic", {}),
            }
        )
        session.add(nota)

        # 3. Produtos
        produtos_data = dados_json.get("Produtos e Serviços", {})

        for ean_key, prod in produtos_data.items():
            quantidade = parse_quantidade(prod.get("Quantidade", "0"))
            valor_unitario = parse_float_br(prod.get("Valor Unitário de Comercialização", prod.get("Valor(R$)", "0")))
            valor_total_prod = parse_float_br(prod.get("valor_total", prod.get("Valor(R$)", "0")))

            # Dados tributários (tudo que não é campo principal)
            campos_principais = {
                "Descrição", "Quantidade", "Unidade Comercial", "Valor(R$)",
                "Código do produto", "Código NCM", "CFOP",
                "Código EAN Comercial", "Valor Unitário de Comercialização",
                "quantidade_registros", "valor_total"
            }
            dados_trib = {k: v for k, v in prod.items() if k not in campos_principais}

            # Vincular ao catálogo interno
            ean_prod = prod.get("Código EAN Comercial", ean_key)
            desc_prod = prod.get("Descrição", "")
            unidade_prod = prod.get("Unidade Comercial", "")
            ncm_prod = prod.get("Código NCM", "")

            catalogo_id = vincular_ao_catalogo(session, ean_prod, desc_prod, unidade_prod, ncm_prod)

            produto = Produto(
                nota_chave=chave_acesso,
                catalogo_id=catalogo_id,
                ean=ean_prod,
                codigo_produto=prod.get("Código do produto", ""),
                descricao=desc_prod,
                ncm=ncm_prod,
                cfop=prod.get("CFOP", ""),
                unidade=unidade_prod,
                quantidade=quantidade,
                valor_unitario=valor_unitario,
                valor_total=valor_total_prod,
                dados_tributarios=dados_trib,
            )
            session.add(produto)

            # 4. Histórico de preços
            preco = PrecoHistorico(
                ean=ean_prod if (ean_prod and ean_prod.upper() != 'SEM GTIN') else f"CAT-{catalogo_id}",
                descricao=desc_prod,
                emitente_cnpj=cnpj,
                data=data_emissao or datetime.utcnow(),
                valor_unitario=valor_unitario,
            )
            session.add(preco)

        # 5. Associar nota ao usuário (se autenticado)
        if user_id:
            user_nota = UserNota(user_id=int(user_id), nota_chave=chave_acesso)
            session.add(user_nota)

        session.commit()
        return chave_acesso

    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()
