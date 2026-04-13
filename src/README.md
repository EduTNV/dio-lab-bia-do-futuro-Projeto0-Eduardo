# Código-Fonte

## Estrutura

```
src/
├── app.py              # Interface Streamlit (chat + sidebar)
├── agente.py           # Orquestrador: monta contexto, chama Gemini, valida resposta
├── analytics.py        # Motor de cálculo financeiro (Pandas)
├── compliance.py       # Middleware de validação de saída (integridade numérica + PII)
├── models.py           # Modelos Pydantic (Transacao, PerfilInvestidor, ContextoSessao)
├── config.py           # Carregamento de variáveis de ambiente
└── requirements.txt    # Dependências do projeto
```

## Como Rodar

```bash
# Na raiz do projeto
pip install -r src/requirements.txt

# Iniciar a aplicação
cd src
streamlit run app.py
```

A aplicação estará disponível em `http://localhost:8501`.

## Variáveis de Ambiente

Copie o `.env.example` da raiz para `.env` e preencha sua chave:

```
GEMINI_API_KEY=sua_chave_do_google_ai_studio
DATA_DIR=data/
```
