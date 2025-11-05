import streamlit as st
import requests
import uuid
import time

API_BASE_URL = "https://fbd5gcxt52.execute-api.us-east-1.amazonaws.com/default"
# --- Nova URL da Função Lambda (para o chat)
CHAT_LAMBDA_URL = "https://pklh47axbxddmctyxabw2gkwba0gxsou.lambda-url.us-east-1.on.aws/"

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

            resposta_completa = "" # Variável para acumular a resposta
            
            try:
                # Chama a rota /chat da sua API
                response = requests.post(f"{CHAT_LAMBDA_URL}/lambda-chatbot-usa", json={
                    "pergunta": prompt,
                    "sessionId": st.session_state["user_session_id"]
                }, stream=True)

                if response.status_code == 200:
                    # 2. Iteramos sobre cada "pedaço" da resposta
                    for chunk in response.iter_content(chunk_size=None, decode_unicode=True):
                        if chunk:
                            resposta_completa += chunk
                            # 3. Atualizamos o placeholder a cada pedaço
                            indicador.markdown(resposta_completa + "▌") # O ▌ dá um efeito de cursor
                    
                    # 4. Remove o cursor no final
                    indicador.markdown(resposta_completa)
                else:
                    resposta_completa = f"Erro na API de chat: {response.text}"
                    indicador.markdown(resposta_completa)

            except Exception as e:
                resposta_completa = f"Erro de conexão: {e}"
                indicador.markdown(resposta_completa)

            # NÃO precisamos mais de 'indicador.empty()' ou 'st.markdown(resposta)'
            # A variável 'indicador' já contém a resposta final.

        # Armazena a resposta COMPLETA
        st.session_state["mensagens"].append({"role": "assistant", "content": resposta_completa})
    
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


