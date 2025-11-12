import streamlit as st
import requests
import uuid
import time

# --- URLs ---
CHAT_LAMBDA_URL = "https://dnbm65zpeghlyum3feleblme5e0njpno.lambda-url.us-east-1.on.aws/" # Sua Lambda URL
URL_AVALIACAO = "https://fbd5gcxt52.execute-api.us-east-1.amazonaws.com/default/lambda-avaliacao" # Sua Lambda de Avaliação

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


# --- FUNÇÃO HELPER PARA EXIBIR MENSAGENS (COM FONTES) ---
def exibir_mensagem(content, role="assistant"):
    """
    Função helper para exibir a mensagem e as fontes.
    """
    # Verifica se é uma resposta da IA (que agora é um dicionário)
    if role == "assistant" and isinstance(content, dict):
        # 1. Exibe a resposta principal
        st.markdown(content.get("resposta", "Erro: Resposta não encontrada"))
        
        # 2. Busca pelos metadados e fontes
        metadata = content.get("metadata", {})
        sources = metadata.get("sources", [])
        
        # 3. Se houver fontes, cria o popover!
        if sources:
            with st.popover("Fontes 📚", use_container_width=True):
                for i, source in enumerate(sources):
                    st.subheader(f"Fonte {i+1}")
                    
                    # Pega o dicionário de localização
                    location = source.get("location", {}) 
                    
                    # --- LÓGICA DE EXIBIÇÃO DA ORIGEM ---
                    if not location:
                        st.markdown("**Origem:** Metadados de origem não disponíveis")
                    
                    else:
                        location_type = location.get("type", "").lower()
                        
                        if location_type == "s3":
                            uri = location.get('uri', 'URI não encontrado')
                            # Extrai apenas o nome do arquivo
                            filename = uri.split('/')[-1]
                            st.markdown(f"**Arquivo (S3):** `{filename}`")
                            
                        elif location_type == "web":
                            url = location.get('url', 'URL não encontrada')
                            st.markdown(f"**Site:** {url}")
                            
                        else:
                            origem_tipo = location.get('type', 'Desconhecida')
                            if not origem_tipo:
                               origem_tipo = "Desconhecida"
                            st.markdown(f"**Origem:** {origem_tipo}")
                    
                    # --- LÓGICA DE EXIBIÇÃO DO CONTEÚDO ---
                    source_content_text = source.get("content", "Sem conteúdo de amostra.")
                    st.caption(source_content_text)
                    
                    if i < len(sources) - 1:
                        st.divider()
    
    else:
        # Se for uma mensagem do usuário (ou uma resposta de erro string)
        st.markdown(content)
# --- FIM DA FUNÇÃO HELPER ---


# ETAPA 1: CHAT ATIVO (MODO BUFFERED)
if not st.session_state["chat_finalizado"]:
    st.caption(f"Session ID: {st.session_state['user_session_id']}")
    
    # Exibe mensagens anteriores usando a função helper
    for msg in st.session_state["mensagens"]:
        with st.chat_message(msg["role"]):
            exibir_mensagem(msg["content"], msg["role"])

    # Input do usuário
    if prompt := st.chat_input("Digite sua pergunta..."):
        # Adiciona a mensagem do usuário ao histórico
        st.session_state["mensagens"].append({"role": "user", "content": prompt})
        
        # Exibe a mensagem do usuário IMEDIATAMENTE
        with st.chat_message("user"):
            st.markdown(prompt)

        # Exibe o "Digitando..." IMEDIATAMENTE
        with st.chat_message("assistant"):
            indicador = st.empty()
            indicador.markdown("💬 Digitando...")

            try:
                # Chama a Lambda
                response = requests.post(CHAT_LAMBDA_URL, json={
                    "pergunta": prompt,
                    "sessionId": st.session_state["user_session_id"]
                })

                if response.status_code == 200:
                    # Salva o JSON COMPLETO no histórico
                    full_response_data = response.json()
                    st.session_state["mensagens"].append({"role": "assistant", "content": full_response_data})
                else:
                    resposta_erro = f"Erro na API de chat: {response.text}"
                    st.session_state["mensagens"].append({"role": "assistant", "content": resposta_erro})

            except Exception as e:
                resposta_erro = f"Erro de conexão: {e}"
                st.session_state["mensagens"].append({"role": "assistant", "content": resposta_erro})

            
            # Força o Streamlit a recarregar
            st.rerun()
    
    # Botão de finalizar (sem alteração)
    if st.button("Finalizar Chat e Avaliar"):
        st.session_state["chat_finalizado"] = True
        st.rerun()

# ETAPA 2: FORMULÁRIO DE AVALIAÇÃO (Sem alteração)
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

# ETAPA 3: TELA DE AGRADECIMENTO (Sem alteração)
else:
    st.success("✅ Avaliação enviada com sucesso! Obrigado pelo seu feedback.")
    st.balloons()
    if st.button("Iniciar Novo Chat"):
        st.session_state["mensagens"] = []
        st.session_state["user_session_id"] = str(uuid.uuid4())
        st.session_state["chat_finalizado"] = False
        st.session_state["avaliacao_enviada"] = False
        st.rerun()
