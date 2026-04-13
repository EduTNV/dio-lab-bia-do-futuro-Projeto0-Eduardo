import os
import json
from typing import List, Dict

import pandas as pd

from models import (
    Transacao,
    PerfilInvestidor,
    ProdutoFinanceiro,
    HistoricoAtendimento,
    ContextoSessao,
    Meta,
)
from config import DATA_DIR_PATH


class MotorAnalytics:
    """Motor de Analytics — processa os CSVs e JSONs com Pandas.

    Regra crítica: nenhum valor financeiro deve ser calculado fora deste arquivo.
    O LLM nunca calcula — apenas recebe o resultado deste módulo.
    """

    def __init__(self) -> None:
        self.transacoes: List[Transacao] = []
        self.perfil: PerfilInvestidor | None = None
        self.produtos: List[ProdutoFinanceiro] = []
        self.historico: List[HistoricoAtendimento] = []

    def carregar_dados(self) -> None:
        """Lê todos os arquivos de data/ e valida via Pydantic."""

        df_transacoes = pd.read_csv(
            os.path.join(DATA_DIR_PATH, "transacoes.csv"),
            encoding="utf-8",
        )
        self.transacoes = [
            Transacao(**row) for row in df_transacoes.to_dict(orient="records")
        ]

        with open(
            os.path.join(DATA_DIR_PATH, "perfil_investidor.json"),
            "r",
            encoding="utf-8",
        ) as f:
            dados_perfil = json.load(f)
        self.perfil = PerfilInvestidor(**dados_perfil)

        with open(
            os.path.join(DATA_DIR_PATH, "produtos_financeiros.json"),
            "r",
            encoding="utf-8",
        ) as f:
            dados_produtos = json.load(f)
        self.produtos = [ProdutoFinanceiro(**p) for p in dados_produtos]

        df_historico = pd.read_csv(
            os.path.join(DATA_DIR_PATH, "historico_atendimento.csv"),
            encoding="utf-8",
        )
        self.historico = [
            HistoricoAtendimento(**row)
            for row in df_historico.to_dict(orient="records")
        ]

    def calcular_margem_livre(self) -> float:
        """Soma entradas, subtrai saídas e retorna a margem livre."""
        df = pd.DataFrame([t.model_dump() for t in self.transacoes])

        total_entradas = df.loc[df["tipo"] == "entrada", "valor"].sum()
        total_saidas = df.loc[df["tipo"] == "saida", "valor"].sum()

        return round(float(total_entradas - total_saidas), 2)

    def gastos_por_categoria(self) -> Dict[str, float]:
        """Retorna o total por categoria, considerando apenas tipo 'saida'."""
        df = pd.DataFrame([t.model_dump() for t in self.transacoes])

        df_saidas = df[df["tipo"] == "saida"]
        agrupado = df_saidas.groupby("categoria")["valor"].sum()

        return {cat: round(float(val), 2) for cat, val in agrupado.items()}

    def filtrar_produtos_por_perfil(
        self, perfil: PerfilInvestidor
    ) -> List[ProdutoFinanceiro]:
        """Remove produtos com risco 'alto' se aceita_risco == False."""
        if not perfil.aceita_risco:
            return [p for p in self.produtos if p.risco != "alto"]
        return list(self.produtos)

    def historico_recente(self, n: int = 2) -> List[HistoricoAtendimento]:
        """Retorna os N atendimentos mais recentes, ordenados por data."""
        ordenado = sorted(self.historico, key=lambda h: h.data, reverse=True)
        return ordenado[:n]

    def montar_contexto_sessao(self) -> ContextoSessao:
        """Agrega todos os dados calculados em um único ContextoSessao."""
        if self.perfil is None:
            raise ValueError(
                "Dados não carregados. Chame carregar_dados() antes de montar o contexto."
            )

        return ContextoSessao(
            perfil=self.perfil,
            margem_livre=self.calcular_margem_livre(),
            gastos_por_categoria=self.gastos_por_categoria(),
            historico_recente=self.historico_recente(),
            produtos_disponiveis=self.filtrar_produtos_por_perfil(self.perfil),
        )
