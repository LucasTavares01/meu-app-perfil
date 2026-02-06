import streamlit as st
import google.generativeai as genai
import json
import re
import traceback

# Configuração da API
genai.configure(api_key="AIzaSyBdiuvsktRme3A2k-HhkoQZU211mP76oV8")

# Tentativa com o nome padrão mais aceito
model = genai.GenerativeModel('gemini-1.5-flash')

# Estilização Visual (Perfil 7)
st.markdown("""
    <style>
    .stApp { background-color: #1e272e; color: white; }
    .card-container { background-color: #d1d8e0; color: #2f3640; padding: 25px; border-radius: 5px; border-left: 15px solid #0984e3; box-shadow: 5px 5px 15px rgba(0,0,0,0.5); }
    .hint-line { border-bottom: 1px solid #7f8c8d; padding: 8px 0; font-family: sans-serif; font-size: 16px; font-weight: bold; }
    .header-text { color: #2f3640; font-weight: bold; margin-bottom: 15px; text-transform: uppercase; border-bottom: 2px solid #2f3640; font-size: 18px; }
    .stButton>button { width: 100%; background-color: #0984e3; color: white; border: none; padding: 15px; font-weight: bold; font-size: 16px; }
    .log-box { background-color: #000; color: #0f0; padding: 10px; font-family: monospace; font-size: 12px; border-radius: 5px; overflow-x: auto; margin-top: 20px; }
    </style>
    """, unsafe_allow_html=True)

if 'carta' not in st.session_state: st.session_state.carta = None
if 'revelado' not in st.session_state: st.session_state.revelado = False
if 'last_log' not in st.session_state: st.session_state.last_log = "Nenhum log disponível."

def gerar_carta():
    prompt = """
    Gere uma carta de Perfil 7 em JSON. 
    Temas: Ano, Pessoa, Lugar, Digital ou Coisa.
    20 dicas (3 fáceis, 7 médias, 10 difíceis) em ordem ALEATÓRIA.
    Especiais: 30% chance de 'PERCA A VEZ' ou 'UM PALPITE A QUALQUER HORA'.
    JSON: {"tema": "...", "dicas": ["1. ", "2. "...], "resposta": "..."}
    """
    try:
        # Tenta gerar o conteúdo
        response = model.generate_content(prompt)
        raw_text = response.text
        st.session_state.last_log = f"Resposta da IA:\n{raw_text}"
        
        match = re.search(r'\{.*\}', raw_text, re.DOTALL)
        if match:
            st.session_state.carta = json.loads(match.group())
            st.session_state.revelado = False
        else:
            st.session_state.last_log += "\nERRO: JSON não encontrado."
    except Exception as e:
        st.session_state.last_log = f"ERRO:\n{traceback.format_exc()}"

st.title("🃏 Perfil 7 AI")

if not st.session_state.carta:
    if st.button("✨ GERAR NOVA CARTA"):
        with st.spinner('Acessando Gemini...'):
            gerar_carta()
            st.rerun()
else:
    c = st.session_state.carta
    st.markdown(f'<div class="card-container"><div class="header-text">Sou um(a): {c.get("tema")}</div>', unsafe_allow_html=True)
    for dica in c.get('dicas', []):
        st.markdown(f"<div class='hint-line'>{dica}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔍 REVELAR"): st.session_state.revelado = True
    with col2:
        if st.button("🔄 OUTRA CARTA"):
            st.session_state.carta = None
            st.rerun()

    if st.session_state.revelado:
        st.success(f"Resposta: {c.get('resposta')}")

with st.expander("🛠️ Logs"):
    st.markdown(f'<div class="log-box">{st.session_state.last_log}</div>', unsafe_allow_html=True)
