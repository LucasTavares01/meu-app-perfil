import streamlit as st
import google.generativeai as genai
import json
import re
import traceback

# --- CONFIGURAÇÃO INICIAL ---
api_key = "AIzaSyBdiuvsktRme3A2k-HhkoQZU211mP76oV8"
genai.configure(api_key=api_key)

# Estilização Visual
st.markdown("""
    <style>
    .stApp { background-color: #1e272e; color: white; }
    .card-container { background-color: #d1d8e0; color: #2f3640; padding: 25px; border-radius: 5px; border-left: 15px solid #0984e3; }
    .hint-line { border-bottom: 1px solid #7f8c8d; padding: 8px 0; font-family: sans-serif; font-size: 16px; font-weight: bold; }
    .header-text { color: #2f3640; font-weight: bold; margin-bottom: 15px; text-transform: uppercase; border-bottom: 2px solid #2f3640; font-size: 18px; }
    .stButton>button { width: 100%; background-color: #0984e3; color: white; border: none; padding: 15px; font-weight: bold; font-size: 16px; }
    .log-box { background-color: #000; color: #0f0; padding: 10px; font-family: monospace; font-size: 11px; border-radius: 5px; overflow-x: auto; margin-top: 20px; }
    </style>
    """, unsafe_allow_html=True)

# Estados da Sessão
if 'carta' not in st.session_state: st.session_state.carta = None
if 'revelado' not in st.session_state: st.session_state.revelado = False
if 'last_log' not in st.session_state: st.session_state.last_log = "Iniciando sistema..."
if 'model_name' not in st.session_state: st.session_state.model_name = None

# --- FUNÇÃO INTELIGENTE DE SELEÇÃO DE MODELO ---
def get_best_model():
    try:
        # Pergunta à API quais modelos estão disponíveis para sua chave
        st.session_state.last_log += "\nListando modelos disponíveis..."
        available_models = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                available_models.append(m.name)
        
        st.session_state.last_log += f"\nModelos encontrados: {available_models}"

        # Tenta achar o Flash, se não, vai no Pro, se não, pega o primeiro que tiver
        if any('flash' in m for m in available_models):
            chosen = next(m for m in available_models if 'flash' in m)
        elif any('gemini-pro' in m for m in available_models):
            chosen = next(m for m in available_models if 'gemini-pro' in m)
        else:
            chosen = available_models[0]
            
        st.session_state.last_log += f"\nModelo escolhido automaticamente: {chosen}"
        return genai.GenerativeModel(chosen)
    except Exception as e:
        st.session_state.last_log += f"\nERRO FATAL AO BUSCAR MODELOS: {e}"
        # Fallback de emergência
        return genai.GenerativeModel('gemini-pro')

# --- FUNÇÃO DE GERAÇÃO ---
def gerar_carta():
    model = get_best_model()
    
    prompt = """
    Aja como um gerador de cartas para o jogo Perfil 7.
    TAREFA: Gere um JSON válido com 1 tema, 20 dicas e 1 resposta.
    REGRAS DE DIFICULDADE: 3 fáceis, 7 médias, 10 difíceis.
    EMBARALHAMENTO: As dicas DEVEM estar em ordem aleatória de dificuldade (não coloque as fáceis primeiro).
    ESPECIAIS: 
    - 30% de chance de incluir 'PERCA A VEZ' (substituindo uma dica média).
    - 30% de chance de incluir 'UM PALPITE A QUALQUER HORA' (substituindo uma dica difícil).
    FORMATO DE RESPOSTA OBRIGATÓRIO (JSON PURO):
    {"tema": "EXEMPLO", "dicas": ["1. Dica A", "2. Dica B", ...], "resposta": "RESPOSTA FINAL"}
    """
    try:
        response = model.generate_content(prompt)
        st.session_state.last_log += f"\n\n--- NOVA GERAÇÃO ---\n{response.text}"
        
        # Limpeza agressiva para encontrar JSON
        match = re.search(r'\{.*\}', response.text, re.DOTALL)
        if match:
            st.session_state.carta = json.loads(match.group())
            st.session_state.revelado = False
        else:
            st.session_state.last_log += "\nERRO: A IA não retornou um JSON válido."
            st.error("Erro na leitura da carta. Tente novamente.")
            
    except Exception as e:
        st.session_state.last_log += f"\nERRO NA GERAÇÃO: {traceback.format_exc()}"
        st.error("Ocorreu um erro. Verifique os logs abaixo.")

# --- INTERFACE ---
st.title("🃏 Perfil 7 AI - Auto-Discovery")

if not st.session_state.carta:
    if st.button("✨ GERAR PRIMEIRA CARTA"):
        with st.spinner('Conectando ao Google e escolhendo o melhor modelo...'):
            gerar_carta()
            st.rerun()
else:
    c = st.session_state.carta
    st.markdown(f'<div class="card-container"><div class="header-text">Sou um(a): {c.get("tema", "???")}</div>', unsafe_allow_html=True)
    
    # Exibe as dicas
    dicas = c.get('dicas', [])
    for dica in dicas:
        st.markdown(f"<div class='hint-line'>{dica}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.write("")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔍 REVELAR"): st.session_state.revelado = True
    with col2:
        if st.button("🔄 NOVA CARTA"):
            st.session_state.carta = None
            st.rerun()

    if st.session_state.revelado:
        st.success(f"RESPOSTA: {c.get('resposta')}")

# Logs sempre visíveis para debug
st.divider()
with st.expander("🛠️ Logs Técnicos (Verifique aqui se der erro)"):
    st.text_area("Log do Sistema:", value=st.session_state.last_log, height=300)
