import streamlit as st
import requests
import uuid

# URL da sua API Gateway
API_URL = "https://fbd5gcxt52.execute-api.us-east-1.amazonaws.com/default/lambda-chatbot-usa"

st.set_page_config(page_title="Chatbot Bedrock", layout="centered")
st.title("🤖 Chatbot - Bedrock Agent")

# --- INICIALIZAÇÃO DO SESSION STATE ---
if "user_session_id" not in st.session_state:
    st.session_state["user_session_id"] = str(uuid.uuid4())

if "mensagens" not in st.session_state:
    st.session_state["mensagens"] = []

# Controla se o chat foi finalizado
if "chat_finalizado" not in st.session_state:
    st.session_state["chat_finalizado"] = False

# NOVO: Controla se a avaliação já foi enviada
if "avaliacao_enviada" not in st.session_state:
    st.session_state["avaliacao_enviada"] = False

# --- LÓGICA DE EXIBIÇÃO EM 3 ETAPAS ---

# ETAPA 1: O CHAT ESTÁ ATIVO
if not st.session_state["chat_finalizado"]:
    st.caption(f"Session ID: {st.session_state['user_session_id']}")
    
    for msg in st.session_state["mensagens"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Digite sua pergunta..."):
        st.session_state["mensagens"].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        try:
            response = requests.post(API_URL, json={
                "pergunta": prompt,
                "sessionId": st.session_state["user_session_id"]
            })
            if response.status_code == 200:
                resposta = response.json().get("resposta", "Sem resposta")
            else:
                resposta = f"Erro: {response.text}"
        except Exception as e:
            resposta = f"Erro de conexão: {e}"

        st.session_state["mensagens"].append({"role": "assistant", "content": resposta})
        with st.chat_message("assistant"):
            st.markdown(resposta)
    
    if st.button("Finalizar Chat e Avaliar"):
        st.session_state["chat_finalizado"] = True
        st.rerun()

# ETAPA 2: FORMULÁRIO DE AVALIAÇÃO (CHAT FINALIZADO, MAS AVALIAÇÃO NÃO ENVIADA)
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
            
            # TODO: Aqui vai a sua lógica para salvar a avaliação
            # Por exemplo, enviar para uma API ou salvar num banco de dados.
            # print(f"ID: {st.session_state['user_session_id']}, Nota: {nota_numero}, Comentário: {comentario}")

            # Define que a avaliação foi enviada e força o recarregamento
            st.session_state["avaliacao_enviada"] = True
            st.rerun()

# ETAPA 3: TELA DE AGRADECIMENTO (AVALIAÇÃO JÁ ENVIADA)
else:
    st.success("✅ Avaliação enviada com sucesso! Obrigado pelo seu feedback.")
    st.balloons()

    # Adiciona um botão para iniciar um novo chat, limpando o estado da sessão
    if st.button("Iniciar Novo Chat"):
        st.session_state["mensagens"] = []
        st.session_state["user_session_id"] = str(uuid.uuid4())
        st.session_state["chat_finalizado"] = False
        st.session_state["avaliacao_enviada"] = False
        st.rerun()
