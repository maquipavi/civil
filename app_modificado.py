import streamlit as st
import google.generativeai as genai
import os
import datetime

# --- Constantes e Configuração Inicial ---
GOOGLE_API_KEY = "AIzaSyBarB5CfRsl_M0nkQjgg-ystWV-CyzN0jU" # Chave API Fixa

# Configura a API do Google
try:
    genai.configure(api_key=GOOGLE_API_KEY)
except Exception as e:
    st.error(f"Erro crítico ao configurar a API do Google com a chave fornecida: {e}")
    st.stop() # Impede a execução do restante do app se a chave for inválida

# --- Configuração da Página Streamlit ---
st.set_page_config(page_title="Guia de Linha Amarela", page_icon="🚜", layout="wide")

# --- Estado da Sessão ---
# Inicializa o estado da sessão se não existir
if 'model' not in st.session_state:
    try:
        st.session_state.model = genai.GenerativeModel(
            model_name='gemini-1.5-flash', # Modelo recomendado
            system_instruction="""Você é um assistente virtual especializado em engenharia civil, focado em máquinas pesadas de linha amarela (escavadeiras, pás-carregadeiras, tratores de esteira, motoniveladoras, rolos compactadores, etc.) e técnicas de pavimentação. Seu objetivo é funcionar como um guia completo para engenheiros, fornecendo informações técnicas precisas, especificações de equipamentos, comparações, boas práticas de operação, manutenção preventiva e corretiva, e auxiliando na resolução de dúvidas relacionadas a essa área. Responda de forma clara, objetiva e profissional, utilizando terminologia técnica apropriada. Se a pergunta for ambígua, peça esclarecimentos. Se não souber a resposta, admita e sugira onde o usuário pode buscar a informação. Evite opiniões pessoais e foque em dados e fatos técnicos. Não forneça informações sobre preços, pois eles variam muito. Se perguntado sobre preços, explique que o usuário deve contatar distribuidores autorizados."""
        )
        st.session_state.chat = st.session_state.model.start_chat(history=[])
        st.session_state.messages = []
        st.session_state.topic_selected = False # Para controlar o estado inicial
    except Exception as e:
        st.error(f"Erro ao inicializar o modelo generativo: {e}")
        st.stop()

# --- Barra Lateral (Menu) ---
st.sidebar.title("Guia de Linha Amarela para Engenheiros")
st.sidebar.image("heavy_equipment_sidebar.jpeg", caption="Guia de Linha Amarela") # Imagem local
st.sidebar.markdown("**Navegue pelos tópicos:**")

topics = [
    "Visão Geral",
    "Tipos de Equipamentos",
    "Aplicações Comuns",
    "Operação Segura e Eficiente",
    "Manutenção Preventiva e Corretiva"
]

# Usando radio buttons para seleção única de tópico
selected_topic = st.sidebar.radio("Selecione um Tópico:", topics, index=0) # Começa com Visão Geral

# Botão para iniciar chat sobre o tópico (opcional, pode iniciar direto)
if st.sidebar.button(f"Iniciar Chat sobre {selected_topic}"):
    st.session_state.topic_selected = True
    # Limpa mensagens anteriores ao mudar de tópico
    st.session_state.messages = [] 
    st.session_state.chat = st.session_state.model.start_chat(history=[]) # Reinicia o chat para novo contexto
    # Envia uma mensagem inicial contextualizando o tópico
    initial_prompt = f"Gere uma introdução sobre '{selected_topic}' no contexto de máquinas pesadas de linha amarela para engenheiros."
    st.session_state.messages.append({"role": "user", "content": initial_prompt})
    try:
        with st.spinner(f"Gerando introdução sobre {selected_topic}..."):
            response = st.session_state.chat.send_message(initial_prompt)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
    except Exception as e:
        st.error(f"Erro ao gerar introdução: {e}")
    st.rerun() # Recarrega para exibir a introdução

st.sidebar.markdown("--- ")
st.sidebar.info("Este assistente utiliza IA Generativa para fornecer informações técnicas. Desenvolvido com ❤️ por Engº Paulo Rogério Veiga Silva!")

# --- Área Principal do Chat ---
st.title(f"🚜 Assistente Técnico: {selected_topic}")

if not st.session_state.topic_selected and selected_topic == "Visão Geral":
     st.info("Bem-vindo ao Guia de Linha Amarela para Engenheiros! Selecione um tópico na barra lateral para começar ou faça uma pergunta geral abaixo.")
     st.session_state.topic_selected = True # Marca como selecionado para não mostrar a msg de novo

# Exibe o histórico de mensagens
if 'messages' in st.session_state:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# Campo de entrada para nova pergunta
if prompt := st.chat_input(f"Faça sua pergunta sobre {selected_topic}..."):
    # Adiciona a mensagem do usuário ao histórico e exibe
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Gera e exibe a resposta do assistente
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("Pensando...")
        try:
            # Verifica se o chat foi iniciado corretamente
            if st.session_state.chat is None:
                 st.error("Erro: A sessão de chat não foi inicializada corretamente. Tente recarregar a página.")
            else:
                response = st.session_state.chat.send_message(prompt)
                message_placeholder.markdown(response.text)
                # Adiciona a resposta do assistente ao histórico
                st.session_state.messages.append({"role": "assistant", "content": response.text})
        except Exception as e:
             message_placeholder.error(f"Desculpe, ocorreu um erro ao processar sua pergunta: {e}")
             # Adiciona uma mensagem de erro ao histórico para contexto
             st.session_state.messages.append({"role": "assistant", "content": f"Erro ao gerar resposta: {e}"})

# --- Funcionalidade para Salvar Conversa ---
if st.session_state.messages: # Só mostra o botão se houver mensagens
    st.markdown("--- ") # Separador
    # Formata a conversa para salvar
    conversation_history = """# Histórico da Conversa - Guia de Linha Amarela\n\n**Tópico:** {}\n**Data:** {}\n\n---\n\n""".format(selected_topic, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    for msg in st.session_state.messages:
        conversation_history += f"**{msg['role'].capitalize()}:**\n{msg['content']}\n\n---\n"
    
    # Gera um nome de arquivo único
    filename = f"historico_assistente_civil_{selected_topic.lower().replace(' ', '_')}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    
    st.download_button(
        label="💾 Salvar Conversa Atual",
        data=conversation_history,
        file_name=filename,
        mime="text/markdown",
        help="Clique para baixar o histórico desta conversa em formato Markdown."
    )


