from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, ForeignKey, JSON, Index
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime
import os
import json
from dotenv import load_dotenv

_root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(_root_dir, '.env'), override=True)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://nfe_user:nfe_dev@localhost:5433/nfe_analyser"
)


def _json_serializer(obj):
    """Serializa JSON preservando acentos (sem escape unicode)."""
    return json.dumps(obj, ensure_ascii=False)


engine = create_engine(DATABASE_URL, echo=False, json_serializer=_json_serializer)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class Emitente(Base):
    __tablename__ = "emitentes"

    cnpj = Column(String(18), primary_key=True)
    razao_social = Column(String(255))
    nome_fantasia = Column(String(255))
    endereco = Column(String(500))
    bairro = Column(String(100))
    cep = Column(String(10))
    municipio = Column(String(100))
    uf = Column(String(2))
    inscricao_estadual = Column(String(20))
    regime_tributario = Column(String(50))

    notas = relationship("Nota", back_populates="emitente")


class Nota(Base):
    __tablename__ = "notas"

    chave_acesso = Column(String(44), primary_key=True)
    emitente_cnpj = Column(String(18), ForeignKey("emitentes.cnpj"), nullable=False)
    numero = Column(String(20))
    serie = Column(String(10))
    data_emissao = Column(DateTime)
    valor_total = Column(Float)
    natureza_operacao = Column(String(100))
    dados_extras = Column(JSON)  # campos variáveis da NFC-e
    criado_em = Column(DateTime, default=datetime.utcnow)

    emitente = relationship("Emitente", back_populates="notas")
    produtos = relationship("Produto", back_populates="nota", cascade="all, delete-orphan")
    users = relationship("User", secondary="users_notas", back_populates="notas")


class Produto(Base):
    __tablename__ = "produtos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nota_chave = Column(String(44), ForeignKey("notas.chave_acesso"), nullable=False)
    ean = Column(String(20), index=True)
    codigo_produto = Column(String(50))
    descricao = Column(String(255))
    ncm = Column(String(10))
    cfop = Column(String(10))
    unidade = Column(String(10))
    quantidade = Column(Float)
    valor_unitario = Column(Float)
    valor_total = Column(Float)
    dados_tributarios = Column(JSON)  # ICMS, IBS, CBS, etc.

    nota = relationship("Nota", back_populates="produtos")

    __table_args__ = (
        Index("ix_produto_ean_nota", "ean", "nota_chave"),
    )


class PrecoHistorico(Base):
    """View materializada como tabela para consultas rápidas de preço."""
    __tablename__ = "precos_historico"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ean = Column(String(20), nullable=False)
    descricao = Column(String(255))
    emitente_cnpj = Column(String(18), ForeignKey("emitentes.cnpj"), nullable=False)
    data = Column(DateTime, nullable=False)
    valor_unitario = Column(Float, nullable=False)

    __table_args__ = (
        Index("ix_preco_ean_emitente_data", "ean", "emitente_cnpj", "data"),
        Index("ix_preco_ean_data", "ean", "data"),
    )


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    criado_em = Column(DateTime, default=datetime.utcnow)

    notas = relationship("Nota", secondary="users_notas", back_populates="users")


class UserNota(Base):
    __tablename__ = "users_notas"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    nota_chave = Column(String(44), ForeignKey("notas.chave_acesso"), primary_key=True)
    associado_em = Column(DateTime, default=datetime.utcnow)


def init_db():
    """Cria todas as tabelas no banco."""
    Base.metadata.create_all(engine)
    print("Tabelas criadas com sucesso!")


if __name__ == "__main__":
    init_db()
