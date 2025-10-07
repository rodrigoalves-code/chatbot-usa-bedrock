import streamlit as st
import requests
import uuid
import time

API_BASE_URL = "https://fbd5gcxt52.execute-api.us-east-1.amazonaws.com/default"

st.set_page_config(page_title="Chatbot Bedrock", layout="centered")
st.title("🤖 Chatbot - Bedrock Agent")

# --- Inicialização do Session State ---
if "user_session_id" not in st.session_state:
    st.session_state["user_session_id"] = str(uuid.uuid4())
if "mensagens" not in st.session_state:
    st.session_state["mensagens"] = []
if "chat_finalizado" not in st.session_state:
    st.session_state["chat_finalizado"] = False
if "avaliacao_enviada" not in st.session_state:
    st.session_state["avaliacao_enviada"] = False

# --- Lógica de Exibição em 3 Etapas ---

# ETAPA 1: CHAT ATIVO
if not st.session_state["chat_finalizado"]:
    st.caption(f"Session ID: {st.session_state['user_session_id']}")
    
    # Exibe mensagens anteriores
    for msg in st.session_state["mensagens"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Input do usuário
    if prompt := st.chat_input("Digite sua pergunta..."):
        st.session_state["mensagens"].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Placeholder pro "digitando..."
        with st.chat_message("assistant"):
            indicador = st.empty()
            indicador.markdown("💬 Digitando...")

            try:
                # Chama a rota /chat da sua API
                response = requests.post(f"{API_BASE_URL}/lambda-chatbot-usa", json={
                    "pergunta": prompt,
                    "sessionId": st.session_state["user_session_id"]
                })

                if response.status_code == 200:
                    resposta = response.json().get("resposta", "Sem resposta")
                else:
                    resposta = f"Erro na API de chat: {response.text}"

            except Exception as e:
                resposta = f"Erro de conexão: {e}"

            # Remove o indicador e mostra resposta final
            indicador.empty()
            st.markdown(resposta)

        # Armazena resposta
        st.session_state["mensagens"].append({"role": "assistant", "content": resposta})
    
    if st.button("Finalizar Chat e Avaliar"):
        st.session_state["chat_finalizado"] = True
        st.rerun()

# ETAPA 2: FORMULÁRIO DE AVALIAÇÃO
elif not st.session_state["avaliacao_enviada"]:
    st.header("Avalie sua experiência")
    st.caption(f"Session ID: {st.session_state['user_session_id']}")
    
    with st.form("evaluation_form"):
        rating_options = {
            "☆☆☆☆☆ (0)": 0, "⭐☆☆☆☆ (1)": 1, "⭐⭐☆☆☆ (2)": 2,
            "⭐⭐⭐☆☆ (3)": 3, "⭐⭐⭐⭐☆ (4)": 4, "⭐⭐⭐⭐⭐ (5)": 5,
        }
        nota_estrelas = st.radio(
            "Sua nota:", options=rating_options.keys(), horizontal=True, index=5
        )
        comentario = st.text_area(
            "Deixe seu comentário (opcional):", max_chars=500, height=150
        )
        submitted = st.form_submit_button("Enviar Avaliação")

        if submitted:
            nota_numero = rating_options[nota_estrelas]
            try:
                URL_AVALIACAO = "https://fbd5gcxt52.execute-api.us-east-1.amazonaws.com/default/lambda-avaliacao"
                payload = {
                    "sessionId": st.session_state['user_session_id'],
                    "nota": nota_numero,
                    "comentario": comentario
                }
                
                response = requests.post(URL_AVALIACAO, json=payload)

                if response.status_code == 200:
                    st.session_state["avaliacao_enviada"] = True
                    st.rerun()
                else:
                    st.error(f"Houve um erro ao enviar sua avaliação. Status: {response.status_code}, Resposta: {response.text}")
            
            except Exception as e:
                st.error(f"Erro de conexão: {e}")

# ETAPA 3: TELA DE AGRADECIMENTO
else:
    st.success("✅ Avaliação enviada com sucesso! Obrigado pelo seu feedback.")
    st.balloons()
    if st.button("Iniciar Novo Chat"):
        st.session_state["mensagens"] = []
        st.session_state["user_session_id"] = str(uuid.uuid4())
        st.session_state["chat_finalizado"] = False
        st.session_state["avaliacao_enviada"] = False
        st.rerun()
