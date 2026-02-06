import streamlit as st
import google.generativeai as genai
import random
import json

# Configuração da sua API
genai.configure(api_key="AIzaSyBdiuvsktRme3A2k-HhkoQZU211mP76oV8")
model = genai.GenerativeModel('gemini-pro')

# Estilização Visual (Cores Perfil 7)
st.markdown("""
    <style>
    .stApp { background-color: #2c3e50; color: white; }
    .card { background-color: #ecf0f1; color: #2c3e50; padding: 20px; border-radius: 10px; border-left: 10px solid #2980b9; }
    .hint-line { border-bottom: 1px solid #bdc3c7; padding: 5px 0; font-family: sans-serif; }
    .stButton>button { width: 100%; background-color: #2980b9; color: white; height: 3em; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

if 'carta' not in st.session_state:
    st.session_state.carta = None

def gerar_carta():
    prompt = """
    Gere uma carta de Perfil 7 em formato JSON. 
    Temas: Ano, Pessoa, Lugar, Digital ou Coisa.
    Regras: 20 dicas. 3 fáceis, 7 médias, 10 difíceis.
    Aleatoriedade: Embaralhe a posição das dificuldades (1 a 20).
    Especiais: 30% de chance de uma média ser 'PERCA A VEZ' e 30% de uma difícil ser 'PALPITE A QUALQUER HORA'.
    Retorne apenas o JSON: {"tema": "", "dicas": ["1. ", "2. "...], "resposta": ""}
    """
    response = model.generate_content(prompt)
    st.session_state.carta = json.loads(response.text)
    st.session_state.revelado = False

# Interface
st.title("🃏 Perfil 7 AI")

if not st.session_state.carta:
    if st.button("✨ GERAR CARTA"):
        gerar_carta()
        st.rerun()
else:
    c = st.session_state.carta
    st.markdown(f"### Diga aos jogadores que sou um(a): **{c['tema']}**")
    
    with st.container():
        for dica in c['dicas']:
            st.markdown(f"<div class='hint-line'>{dica}</div>", unsafe_allow_html=True)
    
    st.divider()
    
    if st.button("🔍 REVELAR RESPOSTA"):
        st.session_state.revelado = True
    
    if st.session_state.get('revelado'):
        st.success(f"RESPOSTA: {c['resposta']}")
    
    if st.button("🔄 NOVA CARTA"):
        st.session_state.carta = None
        st.rerun()
