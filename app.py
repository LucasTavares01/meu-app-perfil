import streamlit as st
import google.generativeai as genai
import json
import re
import traceback

# Configuração da API
genai.configure(api_key="AIzaSyBdiuvsktRme3A2k-HhkoQZU211mP76oV8")
model = genai.GenerativeModel('gemini-1.5-flash')

# Estilização Visual (Perfil 7)
st.markdown("""
    <style>
    .stApp { background-color: #1e272e; color: white; }
    .card-container { background-color: #d1d8e0; color: #2f3640; padding: 25px; border-radius: 5px; border-left: 15px solid #0984e3; }
    .hint-line { border-bottom: 1px solid #7f8c8d; padding: 8px 0; font-family: sans-serif; font-size: 16px; font-weight: bold; }
    .header-text { color: #2f3640; font-weight: bold; margin-bottom: 15px; text-transform: uppercase; border-bottom: 2px solid #2f3640; }
    .stButton>button { width: 100%; background-color: #0984e3; color: white; border: none; padding: 15px; font-weight: bold; }
    .log-box { background-color: #000; color: #0f0; padding: 10px; font-family: monospace; font-size: 12px; border-radius: 5px; overflow-x: auto; }
    </style>
    """, unsafe_allow_html=True)

# Inicialização de estados
if 'carta' not in st.session_state: st.session_state.carta = None
if 'revelado' not in st.session_state: st.session_state.revelado = False
if 'last_log' not in st.session_state: st.session_state.last_log = "Nenhum log disponível."

def gerar_carta():
    prompt = """
    Gere uma carta de Perfil 7. Escolha um tema (Ano, Pessoa, Lugar, Digital ou Coisa).
    Gere 20 dicas únicas e a resposta.
    Dificuldade: 3 fáceis, 7 médias e 10 difíceis, embaralhadas aleatoriamente entre 1 e 20.
    Especiais: 30% de chance de 'PERCA A VEZ' em dicas médias e 30% de 'UM PALPITE A QUALQUER HORA' em dicas difíceis.
    RETORNE APENAS O JSON PURO NO FORMATO: {"tema": "...", "dicas": ["1. ...", "2. ..."], "resposta": "..."}
    """
    try:
        response = model.generate_content(prompt)
        raw_text = response.text
        st.session_state.last_log = f"Resposta da IA:\n{raw_text}"
        
        # Tenta extrair o JSON
        match = re.search(r'\{.*\}', raw_text, re.DOTALL)
        if match:
            json_data = match.group()
            st.session_state.carta = json.loads(json_data)
            st.session_state.revelado = False
        else:
            st.session_state.last_log += "\n\nERRO: JSON não encontrado na resposta."
    except Exception as e:
        st.session_state.last_log = f"ERRO TÉCNICO:\n{traceback.format_exc()}"

# Interface Principal
st.title("🃏 Perfil 7 - AI Edition")

if not st.session_state.carta:
    if st.button("✨ GERAR NOVA CARTA"):
        with st.spinner('Chamando Gemini...'):
            gerar_carta()
            st.rerun()
else:
    c = st.session_state.carta
    st.markdown(f'<div class="card-container"><div class="header-text">Sou um(a): {c.get("tema", "Desconhecido")}</div>', unsafe_allow_html=True)
    for dica in c.get('dicas', []):
        st.markdown(f"<div class='hint-line'>{dica}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔍 REVELAR"): st.session_state.revelado = True
    with col2:
        if st.button("🔄 NOVA CARTA"):
            st.session_state.carta = None
            st.rerun()

    if st.session_state.revelado:
        st.success(f"RESPOSTA: {c.get('resposta', 'N/A')}")

# Seção de Logs (Debug)
st.divider()
with st.expander("🛠️ Ver Logs de Depuração (O que está acontecendo?)"):
    st.markdown(f'<div class="log-box">{st.session_state.last_log}</div>', unsafe_allow_html=True)
