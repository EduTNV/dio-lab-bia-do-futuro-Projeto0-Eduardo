# Base de Conhecimento

## Dados Utilizados

| Arquivo | Formato | Utilização no Agente |
|---------|---------|----------------------|
| `transacoes.csv` | CSV | Alimenta o Motor de Analytics (Pandas) para cálculo de gastos por categoria, margem livre mensal e identificação de padrões de consumo |
| `perfil_investidor.json` | JSON | Define o perímetro de atuação do VIT: perfil de risco, objetivos, metas com prazo e tolerância a volatilidade |
| `produtos_financeiros.json` | JSON | Base de produtos consultada para contextualizar simulações — o VIT nunca recomenda produto fora desse catálogo |
| `historico_atendimento.csv` | CSV | Fornece contexto de interações anteriores para evitar repetição e personalizar a abordagem da sessão atual |

**Datasets de referência para expansão futura:** [Hugging Face — Financial Datasets](https://huggingface.co/datasets?search=finance)

---

## Adaptações nos Dados

Os arquivos mockados foram utilizados sem alteração estrutural, mas com duas decisões de design relevantes para o VIT:

**`transacoes.csv`:** o Pandas processa apenas as transações do tipo `saida` para o cálculo de gastos por categoria. A única entrada (`Salário, R$ 5.000`) é tratada como renda de referência. Em produção, essa separação seria feita via campo `tipo` com validação de schema — aqui ela é assumida como confiável por ser dado sintético.

**`perfil_investidor.json`:** o campo `aceita_risco: false` funciona como trava sistêmica. Quando presente, o VIT filtra automaticamente do catálogo de produtos qualquer item com `risco: alto` — independente do que o usuário solicitar na conversa. Isso é aplicado no backend antes da montagem do prompt, não pelo LLM.

---

## Estratégia de Integração

### Como os dados são carregados?

Todos os arquivos são carregados no início da sessão pelo backend FastAPI, antes de qualquer chamada ao LLM. O fluxo é:

1. `perfil_investidor.json` é lido e validado via Pydantic
2. `transacoes.csv` é processado pelo Pandas, que gera os agregados (totais por categoria, margem livre)
3. `produtos_financeiros.json` é filtrado com base no perfil de risco do cliente
4. `historico_atendimento.csv` é lido para extrair os dois atendimentos mais recentes como contexto de continuidade

Nenhum arquivo bruto é enviado ao LLM. Apenas os agregados e resumos calculados pelo backend compõem o contexto do prompt.

### Como os dados são usados no prompt?

Os dados vão no **system prompt** como contexto estruturado de sessão, montado pelo orquestrador. O LLM não consulta os arquivos diretamente — ele recebe um bloco de texto pré-formatado com os valores já calculados e validados. Isso é o que impede alucinações matemáticas: o modelo não tem o que calcular, apenas o que comunicar.

---

## Exemplo de Contexto Montado

Abaixo está um exemplo real do bloco de contexto gerado pelo backend a partir dos arquivos desta base, formatado para injeção no system prompt do VIT:

```
[CONTEXTO DA SESSÃO - NÃO DIVULGAR AO USUÁRIO]

Perfil do Cliente:
- Nome: João Silva
- Idade: 32 anos | Profissão: Analista de Sistemas
- Perfil de risco: Moderado | Aceita volatilidade: Não
- Objetivo principal: Completar reserva de emergência (falta R$ 5.000 — prazo: jun/2026)
- Meta secundária: Entrada do apartamento (R$ 50.000 — prazo: dez/2027)

Situação Financeira (processada pelo backend):
- Renda mensal: R$ 5.000,00
- Total de saídas (out/2025): R$ 2.488,90
- Margem livre estimada: R$ 2.511,10

Gastos por Categoria (out/2025):
- Moradia: R$ 1.380,00 (55,4% dos gastos fixos)
- Alimentação: R$ 570,00
- Transporte: R$ 295,00
- Saúde: R$ 188,00
- Lazer: R$ 55,90

Histórico Recente (últimos 2 atendimentos):
- out/2025: Cliente acompanhou progresso da reserva de emergência
- out/2025: Cliente perguntou sobre Tesouro Selic

Produtos disponíveis para este perfil (risco baixo e médio):
- Tesouro Selic | Renda Fixa | 100% Selic | Aporte mín: R$ 30
- CDB Liquidez Diária | Renda Fixa | 102% CDI | Aporte mín: R$ 100
- LCI/LCA | Renda Fixa | 95% CDI | Aporte mín: R$ 1.000 | Carência: 90 dias
- Fundo Multimercado | Fundo | CDI+2% | Aporte mín: R$ 500

[Produtos com risco alto suprimidos por perfil: aceita_risco = false]

REGRAS DESTA SESSÃO:
- Cite a origem de cada dado ao apresentá-lo ao usuário
- Não realize cálculos — use apenas os valores acima
- Não mencione produtos fora da lista filtrada
- Se questionado sobre cotações em tempo real, acione o fallback de escopo
```
