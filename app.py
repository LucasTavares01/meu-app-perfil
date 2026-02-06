import streamlit as st
import google.generativeai as genai
import json
import re
import traceback

# --- CONFIGURAÇÃO DE SEGURANÇA ---
try:
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
        genai.configure(api_key=api_key)
    else:
        api_key = "COLOQUE_SUA_KEY_AQUI_SE_ESTIVER_RODANDO_LOCAL" 
        genai.configure(api_key=api_key)
except Exception:
    st.error("ERRO: Configure sua chave no painel 'Secrets' do Streamlit.")
    st.stop()

# --- CSS (ESTILO VISUAL) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;800&display=swap');

    /* Fundo Mágico */
    .stApp {
        background: rgb(40,15,65);
        background: linear-gradient(135deg, rgba(40,15,65,1) 0%, rgba(86,22,86,1) 30%, rgba(186,75,35,1) 65%, rgba(232,183,77,1) 100%);
        background-size: cover;
        background-attachment: fixed;
        font-family: 'Montserrat', sans-serif;
    }

    #MainMenu, footer, header {visibility: hidden;}
    .main .block-container { padding-top: 2rem; }

    /* Centralizar Spinner */
    div[data-testid="stSpinner"] {
        justify-content: center;
        color: #F3C623;
        font-weight: bold;
        margin-top: 10px;
        margin-bottom: 10px;
    }

    /* --- TELA DE BOAS-VINDAS --- */
    .welcome-box {
        text-align: center;
        padding: 20px;
        margin-bottom: 20px;
        display: flex;
        flex-direction: column;
        align-items: center;
    }
    
    /* DADO DOURADO (Topo) */
    .golden-dice-icon {
        width: 140px; /* Tamanho bom */
        display: block;
        margin-bottom: 10px;
        filter: drop-shadow(0 0 20px rgba(255, 215, 0, 0.6));
        animation: floater 3s ease-in-out infinite;
    }
    @keyframes floater {
        0% { transform: translateY(0px); }
        50% { transform: translateY(-10px); }
        100% { transform: translateY(0px); }
    }
    
    /* TÍTULO PERFIL 7 - ESTILO NEON (Embaixo do dado) */
    .main-title {
        font-family: 'Montserrat', sans-serif;
        font-size: 70px;
        font-weight: 800;
        color: #FFD700; /* Dourado */
        margin: 0;
        /* Efeito Neon/Glow Aura */
        text-shadow: 
            0 0 10px rgba(255, 215, 0, 0.8),
            0 0 20px rgba(255, 165, 0, 0.6),
            0 0 40px rgba(255, 69, 0, 0.4);
        text-align: center;
        line-height: 1.1;
        letter-spacing: 1px;
    }
    
    .subtitle {
        font-size: 28px;
        font-weight: 400;
        color: #ffffff;
        margin-top: 5px;
        margin-bottom: 30px;
        text-shadow: 0 2px 5px rgba(0,0,0,0.5);
        text-align: center;
    }

    /* --- BOTÃO DOURADO (Tela Inicial) --- */
    /* Centralização forçada do container do botão */
    div.stButton {
        display: flex;
        justify-content: center; 
    }

    .stButton > button {
        background: linear-gradient(90deg, #ff9f43, #feca57, #ff9f43);
        background-size: 200% auto;
        color: #5d2e01;
        font-weight: 800;
        font-size: 18px;
        /* Tamanho pílula (padding controla a largura baseada no texto) */
        padding: 15px 40px; 
        border-radius: 50px !important;
        border: 2px solid #fff200;
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        transition: 0.3s;
        text-transform: uppercase;
        margin-top: 10px;
    }
    .stButton > button:hover {
        background-position: right center;
        transform: translateY(-2px);
        box-shadow: 0 10px 25px rgba(255, 200, 0, 0.4);
        color: #000;
    }

    /* --- ESTILO DAS CARTAS (MANTIDO PERFEITO) --- */
    .card-theme-box {
        background: #ffffff;
        padding: 20px;
        border-radius: 15px;
        text-align: center;
        border: 4px solid #FFD700;
        box-shadow: 0 10px 20px rgba(0,0,0,0.3);
        margin-bottom: 20px;
    }
    .header-label { font-size: 12px; color: #95a5a6; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px;}
    .theme-value { font-size: 32px; color: #2c3e50; font-weight: 900; text-transform: uppercase; margin: 0; line-height: 1; }

    .card-tips-box {
        background: #ffffff;
        padding: 10px 20px;
        border-radius: 15px;
        border: 4px solid #FFD700;
        box-shadow: 0 10px 20px rgba(0,0,0,0.3);
        margin-top: 20px;
        margin-bottom: 20px;
    }

    .hint-row { 
        border-bottom: 1px solid #e0e0e0; 
        padding: 12px 5px; 
        font-family: 'Montserrat', sans-serif; 
        font-size: 16px; 
        font-weight: 700; 
        color: #1e272e;
        line-height: 1.4;
    }
    
    .special-loss { background-color: #ff7675; color: white !important; padding: 12px; border-radius: 8px; border: none; text-align: center; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
    .special-guess { background-color: #2ed573; color: white !important; padding: 12px; border-radius: 8px; border: none; text-align: center; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
    
    /* Botões da tela da carta (Ocupam a largura total da coluna) */
    div[data-testid="column"] .stButton > button {
        width: 100%;
    }

    .stSuccess { text-align: center; font-weight: bold; font-size: 18px; border-radius: 15px; }
    </style>
    """, unsafe_allow_html=True)

# --- ESTADOS ---
if 'carta' not in st.session_state: st.session_state.carta = None
if 'revelado' not in st.session_state: st.session_state.revelado = False

# --- FUNÇÕES ---
def get_model():
    try:
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        if any('gemini-1.5-flash' in m for m in models): return genai.GenerativeModel('gemini-1.5-flash')
        if any('gemini-2.5-flash' in m for m in models): return genai.GenerativeModel('gemini-2.5-flash')
        return genai.GenerativeModel('gemini-pro')
    except:
        return genai.GenerativeModel('gemini-pro')

def gerar_carta():
    model = get_model()
    prompt = """
    Jogo 'Perfil 7'. Gere JSON.
    1. TEMA: "PESSOA", "LUGAR", "ANO", "DIGITAL" ou "COISA".
    2. CONTEÚDO: 20 dicas (3 fáceis, 7 médias, 10 difíceis) em ORDEM ALEATÓRIA.
    3. REGRAS DE ITENS ESPECIAIS (MÁXIMO 1 DE CADA):
       - 30% chance 'PERCA A VEZ' (substitui UMA dica média).
       - 30% chance 'UM PALPITE A QUALQUER HORA' (substitui UMA dica difícil).
    FORMATO JSON: {"tema": "PESSOA", "dicas": ["1. Dica...", "2. PERCA A VEZ", ...], "resposta": "RESPOSTA"}
    """
    try:
        response = model.generate_content(prompt)
        text = response.text.replace("```json", "").replace("```", "").strip()
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            st.session_state.carta = json.loads(match.group())
            st.session_state.revelado = False
        else:
            st.error("Erro na IA.")
    except Exception as e:
        st.error(f"Erro: {e}")

# --- INTERFACE ---

if not st.session_state.carta:
    # --- TELA INICIAL RESTAURADA E AJUSTADA ---
    # Ordem: Dado -> Título -> Subtitle
    st.markdown("""
        <div class="welcome-box">
            <img src="https://cdn-icons-png.flaticon.com/512/566/566082.png" class="golden-dice-icon">
            <h1 class="main-title">Perfil 7</h1>
            <div class="subtitle">Bem-vindo!</div>
        </div>
    """, unsafe_allow_html=True)
    
    # Botão Centralizado (Sem use_container_width para respeitar o tamanho do texto)
    if st.button("✨ GERAR NOVA CARTA"):
        with st.spinner('Sorteando...'):
            gerar_carta()
            st.rerun()

else:
    # --- TELA DA CARTA (INTACTA) ---
    c = st.session_state.carta
    
    st.markdown(f"""
    <div class="card-theme-box">
        <div class="header-label">DIGA AOS JOGADORES QUE SOU UM(A):</div>
        <div class="theme-value">{c.get('tema', 'TEMA')}</div>
    </div>
    """, unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        if st.button("👁️ REVELAR RESPOSTA", use_container_width=True): 
            st.session_state.revelado = True

    if st.session_state.revelado:
        st.success(f"🏆 {c.get('resposta')}")

    tips_html = '<div class="card-tips-box">'
    for dica in c.get('dicas', []):
        d_up = dica.upper()
        if "PERCA A VEZ" in d_up:
            tips_html += f"<div class='hint-row special-loss'>🚫 {dica}</div>"
        elif "PALPITE" in d_up:
            tips_html += f"<div class='hint-row special-guess'>💡 {dica}</div>"
        else:
            tips_html += f"<div class='hint-row'>{dica}</div>"
    tips_html += '</div>'
    
    st.markdown(tips_html, unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        if st.button("🔄 NOVA CARTA", use_container_width=True):
            st.session_state.carta = None
            st.rerun()
