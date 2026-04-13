import re
from typing import Tuple, List, Set

from models import ContextoSessao


FALLBACK_RESPOSTA = (
    "Desculpe, não consegui gerar uma resposta adequada neste momento. "
    "Poderia reformular sua pergunta ou tentar novamente em instantes?"
)

TOLERANCIA_MONETARIA = 0.10


class CamadaCompliance:
    """Middleware de Compliance — valida a saída do LLM antes da entrega ao usuário.

    Duas verificações são executadas em sequência:
    1. Integridade numérica — detecta valores monetários fabricados pelo LLM
    2. Detecção de PII — bloqueia exposição de CPF ou conta bancária
    """

    RE_VALORES_MONETARIOS = re.compile(r"R\$\s*[\d.,]+")

    RE_CPF = re.compile(r"\d{3}\.?\d{3}\.?\d{3}-?\d{2}")
    RE_CONTA_BANCARIA = re.compile(r"\d{4,6}-?\d{1}")

    def __init__(self) -> None:
        self.total_bloqueios: int = 0

    def validar(
        self, resposta: str, contexto: ContextoSessao
    ) -> Tuple[bool, str]:
        """Valida a resposta do LLM contra o contexto da sessão.

        Retorna:
            (True, resposta) se aprovado
            (False, mensagem_fallback) se bloqueado
        """

        # Verificação 1 — Integridade numérica
        aprovado, motivo = self._verificar_integridade_numerica(resposta, contexto)
        if not aprovado:
            self.total_bloqueios += 1
            return (False, FALLBACK_RESPOSTA)

        # Verificação 2 — Detecção de PII
        aprovado, motivo = self._detectar_pii(resposta)
        if not aprovado:
            self.total_bloqueios += 1
            return (False, FALLBACK_RESPOSTA)

        return (True, resposta)

    def _verificar_integridade_numerica(
        self, resposta: str, contexto: ContextoSessao
    ) -> Tuple[bool, str]:
        """Extrai valores monetários da resposta e compara com o contexto.

        Valores que divergem de qualquer valor conhecido no contexto (e não
        são somas/subtrações diretas desses valores) são bloqueados.
        """
        valores_resposta = self._extrair_valores(resposta)
        if not valores_resposta:
            return (True, "")

        valores_contexto = self._coletar_valores_contexto(contexto)
        combinacoes_validas = self._gerar_combinacoes_validas(valores_contexto)

        for valor in valores_resposta:
            if not self._valor_e_valido(valor, valores_contexto, combinacoes_validas):
                return (False, f"Valor R$ {valor:.2f} não encontrado no contexto")

        return (True, "")

    def _extrair_valores(self, texto: str) -> List[float]:
        """Extrai todos os valores monetários de um texto."""
        matches = self.RE_VALORES_MONETARIOS.findall(texto)
        valores = []
        for val in matches:
            limpo = val.replace("R$", "").replace(" ", "")
            if "," in limpo and "." in limpo:
                limpo = limpo.replace(".", "").replace(",", ".")
            elif "," in limpo:
                limpo = limpo.replace(",", ".")
            try:
                valor = float(limpo)
                valores.append(valor)
            except ValueError:
                continue
        return valores

    def _coletar_valores_contexto(self, contexto: ContextoSessao) -> Set[float]:
        """Coleta todos os valores numéricos presentes no ContextoSessao."""
        valores = set()

        valores.add(contexto.margem_livre)
        valores.add(contexto.perfil.renda_mensal)
        valores.add(contexto.perfil.patrimonio_total)
        valores.add(contexto.perfil.reserva_emergencia_atual)
        valores.add(float(contexto.perfil.idade))

        for m in contexto.perfil.metas:
            valores.add(m.valor_necessario)

        for gasto in contexto.gastos_por_categoria.values():
            valores.add(gasto)

        total_saidas = sum(contexto.gastos_por_categoria.values())
        valores.add(round(total_saidas, 2))

        for prod in contexto.produtos_disponiveis:
            valores.add(prod.aporte_minimo)

        return valores

    def _gerar_combinacoes_validas(self, valores: Set[float]) -> Set[float]:
        """Gera somas e subtrações diretas dos valores do contexto."""
        combinacoes = set()
        lista_valores = list(valores)

        for i in range(len(lista_valores)):
            for j in range(len(lista_valores)):
                if i != j:
                    soma = round(lista_valores[i] + lista_valores[j], 2)
                    diff = round(abs(lista_valores[i] - lista_valores[j]), 2)
                    combinacoes.add(soma)
                    combinacoes.add(diff)

        return combinacoes

    def _valor_e_valido(
        self,
        valor: float,
        valores_contexto: Set[float],
        combinacoes_validas: Set[float],
    ) -> bool:
        """Verifica se um valor está dentro da tolerância dos valores conhecidos."""
        for v in valores_contexto:
            if abs(valor - v) <= TOLERANCIA_MONETARIA:
                return True

        for v in combinacoes_validas:
            if abs(valor - v) <= TOLERANCIA_MONETARIA:
                return True

        return False

    def _detectar_pii(self, resposta: str) -> Tuple[bool, str]:
        """Detecta padrões de CPF ou conta bancária na resposta."""
        if self.RE_CPF.search(resposta):
            return (False, "PII detectado: padrão de CPF")

        if self.RE_CONTA_BANCARIA.search(resposta):
            return (False, "PII detectado: padrão de conta bancária")

        return (True, "")
