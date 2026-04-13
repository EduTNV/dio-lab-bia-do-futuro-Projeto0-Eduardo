from datetime import date
from typing import List, Dict
from pydantic import BaseModel, Field

class Transacao(BaseModel):
    data: date
    descricao: str
    categoria: str
    valor: float
    tipo: str

class Meta(BaseModel):
    meta: str
    valor_necessario: float
    prazo: str

class PerfilInvestidor(BaseModel):
    nome: str
    idade: int
    profissao: str
    renda_mensal: float
    perfil_investidor: str
    objetivo_principal: str
    patrimonio_total: float
    reserva_emergencia_atual: float
    aceita_risco: bool
    metas: List[Meta]

class ProdutoFinanceiro(BaseModel):
    nome: str
    categoria: str
    risco: str
    rentabilidade: str
    aporte_minimo: float
    indicado_para: str

class HistoricoAtendimento(BaseModel):
    data: date
    canal: str
    tema: str
    resumo: str
    resolvido: str

class ContextoSessao(BaseModel):
    perfil: PerfilInvestidor
    margem_livre: float
    gastos_por_categoria: Dict[str, float]
    historico_recente: List[HistoricoAtendimento]
    produtos_disponiveis: List[ProdutoFinanceiro]
