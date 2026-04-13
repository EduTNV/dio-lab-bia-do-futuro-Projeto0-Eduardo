import streamlit as st
from google.genai import types
from agente import AgenteVIT

st.set_page_config(
    page_title="VIT — Planejador Financeiro",
    page_icon="💰",
    layout="centered",
    initial_sidebar_state="expanded",
)

if "agente_inicializado" not in st.session_state:
    st.session_state.agente_inicializado = False
    st.session_state.agente = None
    st.session_state.contexto = None
    st.session_state.historico_mensagens = []
    st.session_state.historico_api = []

if not st.session_state.agente_inicializado:
    try:
        agente = AgenteVIT()
        agente.inicializar_sessao()
        st.session_state.agente = agente
        st.session_state.contexto = agente.contexto
        st.session_state.agente_inicializado = True
    except Exception as e:
        st.error(
            "Não foi possível inicializar o agente. "
            "Verifique se a GEMINI_API_KEY está configurada no arquivo .env e se os arquivos de dados estão na pasta data/."
        )
        st.stop()

# Referências rápidas
agente: AgenteVIT = st.session_state.agente
contexto = st.session_state.contexto

with st.sidebar:
    st.title("VIT — Planejador Financeiro")
    st.divider()

    st.subheader("Resumo da Sessão")

    st.markdown(f"**Cliente:** {contexto.perfil.nome}")

    margem_formatada = f"R$ {contexto.margem_livre:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    st.metric(label="Margem livre do mês", value=margem_formatada)

    if contexto.perfil.metas:
        meta_principal = contexto.perfil.metas[0]
        valor_atual = contexto.perfil.reserva_emergencia_atual
        valor_total = meta_principal.valor_necessario
        progresso = min(valor_atual / valor_total, 1.0) if valor_total > 0 else 0.0

        st.markdown(f"**Meta:** {meta_principal.meta}")
        st.progress(
            progresso,
            text=f"R$ {valor_atual:,.2f} / R$ {valor_total:,.2f} ({progresso:.0%})".replace(",", "X").replace(".", ",").replace("X", "."),
        )

    st.divider()
    st.caption("⚠️ Dados sintéticos para fins de demonstração.")

if not st.session_state.historico_mensagens:
    with st.spinner("VIT está analisando..."):
        boas_vindas = agente.gerar_boas_vindas()

    st.session_state.historico_mensagens.append(
        {"role": "assistant", "content": boas_vindas}
    )
    st.session_state.historico_api.append(
        types.Content(
            role="model",
            parts=[types.Part.from_text(text=boas_vindas)],
        )
    )

for msg in st.session_state.historico_mensagens:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Digite sua mensagem..."):
    with st.chat_message("user"):
        st.markdown(prompt)

    st.session_state.historico_mensagens.append(
        {"role": "user", "content": prompt}
    )

    with st.chat_message("assistant"):
        with st.spinner("VIT está analisando..."):
            resultado = agente.processar_mensagem(
                mensagem_usuario=prompt,
                historico_conversa=st.session_state.historico_api,
            )
        resposta = resultado["resposta"]
        st.markdown(resposta)

    st.session_state.historico_mensagens.append(
        {"role": "assistant", "content": resposta}
    )
    st.session_state.historico_api.append(
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=prompt)],
        )
    )
    st.session_state.historico_api.append(
        types.Content(
            role="model",
            parts=[types.Part.from_text(text=resposta)],
        )
    )

    st.rerun()
