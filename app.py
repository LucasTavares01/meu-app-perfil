import streamlit as st
import google.generativeai as genai
import json
import re
import traceback

# Configuração da API - Usando sua chave fornecida
genai.configure(api_key="AIzaSyBdiuvsktRme3A2k-HhkoQZU211mP76oV8")

# Nome técnico completo para evitar erro de 'Model Not Found'
model = genai.GenerativeModel('gemini-1.5-flash-latest')

# Estilização Visual (Inspirada no Perfil 7)
st.markdown("""
    <style>
    .stApp { background-color: #1e272e; color: white; }
    .card-container { background-color: #d1d8e0; color: #2f3640; padding: 25px; border-radius: 5px; border-left: 15px solid #0984e3; box-shadow: 5px 5px 15px rgba(0,0,0,0.5); }
    .hint-line { border-bottom: 1px solid #7f8c8d; padding: 8px 0; font-family: sans-serif; font-size: 16px; font-weight: bold; }
    .header-text { color: #2f3640; font-weight: bold; margin-bottom: 15px; text-transform: uppercase; border-bottom: 2px solid #2f3640; font-size: 18px; }
    .stButton>button { width: 100%; background-color: #0984e3; color: white; border: none; padding: 15px; font-weight: bold; font-size: 16px; transition: 0.3s; }
    .stButton>button:hover { background-color: #74b9ff; }
    .log-box { background-color: #000; color: #0f0; padding: 10px; font-family: monospace; font-size: 12px; border-radius: 5px; overflow-x: auto; margin-top: 20px; }
    </style>
    """, unsafe_allow_html=True)

# Inicialização de estados da sessão
if 'carta' not in st.session_state: st.session_state.carta = None
if 'revelado' not in st.session_state: st.session_state.revelado = False
if 'last_log' not in st.session_state: st.session_state.last_log = "Nenhum log disponível."

def gerar_carta():
    prompt = """
    Gere uma carta de Perfil 7. Escolha um tema (Ano, Pessoa, Lugar, Digital ou Coisa).
    Gere 20 dicas únicas e a resposta correta.
    Dificuldade: 3 fáceis, 7 médias e 10 difíceis.
    REGRAS DE EMBARALHAMENTO: As posições de dificuldade devem ser TOTALMENTE ALEATÓRIAS (1 a 20).
    EVENTOS ESPECIAIS:
    - 30% de chance de uma dica média ser 'PERCA A VEZ'.
    - 30% de chance de uma dica difícil ser 'UM PALPITE A QUALQUER HORA'.
    Estes eventos são independentes.
    RETORNE APENAS O JSON: {"tema": "...", "dicas": ["1. ", "2. "...], "resposta": "..."}
    """
    try:
        response = model.generate_content(prompt)
        raw_text = response.text
        st.session_state.last_log = f"Resposta Bruta da IA:\n{raw_text}"
        
        # Extração de JSON usando Regex para evitar textos extras da IA
        match = re.search(r'\{.*\}', raw_text, re.DOTALL)
        if match:
            json_data = match.group()
            st.session_state.carta = json.loads(json_data)
            st.session_state.revelado = False
        else:
            st.session_state.last_log += "\n\nERRO: JSON não detectado na resposta."
    except Exception as e:
        st.session_state.last_log = f"ERRO NO PROCESSO:\n{traceback.format_exc()}"

# --- INTERFACE PRINCIPAL ---
st.title("🃏 Perfil 7 AI")

if not st.session_state.carta:
    st.write("Clique no botão abaixo para gerar uma carta aleatória usando IA.")
    if st.button("✨ GERAR NOVA CARTA"):
        with st.spinner('A IA está pensando na carta...'):
            gerar_carta()
            st.rerun()
else:
    c = st.session_state.carta
    # Renderização da Carta Estilizada
    st.markdown(f"""
    <div class="card-container">
        <div class="header-text">Diga aos jogadores que sou um(a): {c.get('tema', 'TEMA')}</div>
    """, unsafe_allow_html=True)
    
    for dica in c.get('dicas', []):
        st.markdown(f"<div class='hint-line'>{dica}</div>", unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.write("") # Espaçamento
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔍 REVELAR RESPOSTA"):
            st.session_state.revelado = True
    with col2:
        if st.button("🔄 OUTRA CARTA"):
            st.session_state.carta = None
            st.rerun()

    if st.session_state.revelado:
        st.success(f"A resposta é: **{c.get('resposta', 'Erro ao carregar')}**")

# --- SEÇÃO DE DEBUG ---
st.divider()
with st.expander("🛠️ Logs de Sistema (Caso o botão não funcione)"):
    st.markdown(f'<div class="log-box">{st.session_state.last_log}</div>', unsafe_allow_html=True)
