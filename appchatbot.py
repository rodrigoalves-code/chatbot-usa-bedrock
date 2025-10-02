import streamlit as st
import requests
import uuid

# URL da sua API Gateway
API_URL = "https://fbd5gcxt52.execute-api.us-east-1.amazonaws.com/default/lambda-chatbot-usa"

st.set_page_config(page_title="Chatbot Bedrock", layout="centered")
st.title("🤖 Chatbot - Bedrock Agent")

# Cada visitante recebe um session_id único
if "user_session_id" not in st.session_state:
    st.session_state["user_session_id"] = str(uuid.uuid4())

# Histórico de mensagens por visitante
if "mensagens" not in st.session_state:
    st.session_state["mensagens"] = []

# Exibe histórico
for msg in st.session_state["mensagens"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Campo de input do usuário
if prompt := st.chat_input("Digite sua pergunta..."):
    st.session_state["mensagens"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Chama API Lambda passando session_id
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

    # Mostra resposta e adiciona no histórico
    st.session_state["mensagens"].append({"role": "assistant", "content": resposta})
    with st.chat_message("assistant"):
        st.markdown(resposta)
