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
    /* Importando fontes: Montserrat (textos) e Kaushan Script (título neon) */
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;800&family=Kaushan+Script&display=swap');

    /* Fundo Mágico */
    .stApp {
        background: rgb(40,15,65);
        background: linear-gradient(135deg, rgba(40,15,65,1) 0%, rgba(86,22,86,1) 30%, rgba(186,75,35,1) 65%, rgba(232,183,77,1) 100%);
        background-size: cover;
        background-attachment: fixed;
        font-family: 'Montserrat', sans-serif;
    }

    #MainMenu, footer, header {visibility: hidden;}
    .main .block-container { padding-top: 1rem; } /* Menos espaço no topo */

    /* Centralizar Spinner */
    div[data-testid="stSpinner"] {
        justify-content: center;
        color: #F3C623;
        font-weight: bold;
        margin-top: 10px;
        margin-bottom: 10px;
    }

    /* --- TELA DE BOAS-VINDAS (ESTILO NEON SCRIPT) --- */
    .welcome-box {
        text-align: center;
        padding: 10px;
        margin-bottom: 20px;
        position: relative; /* Para o z-index funcionar */
    }
    
    .golden-dice-icon {
        width: 150px; /* Um pouco maior */
        display: block;
        margin: 0 auto;
        /* Brilho ajustado e posição para ficar atrás do texto */
        filter: drop-shadow(0 0 30px rgba(243, 198, 35, 0.5));
        animation: floater 3s ease-in-out infinite;
        position: relative;
        z-index: 0; /* Fica atrás do título */
        margin-top: -60px; /* Puxa para cima para ficar atrás do texto */
        opacity: 0.9;
    }
    @keyframes floater {
        0% { transform: translateY(0px); }
        50% { transform: translateY(-10px); }
        100% { transform: translateY(0px); }
    }
    
    /* TÍTULO PRINCIPAL - NEON SCRIPT GIGANTE */
    .main-title {
        font-family: 'Kaushan Script', cursive; /* Fonte estilo script */
        font-size: 110px; /* Tamanho gigante */
        color: #ffffff; /* Núcleo branco do neon */
        margin: 0;
        padding-top: 20px;
        position: relative;
        z-index: 1; /* Fica na frente do dado */
        /* Efeito de aura neon multicamadas intenso */
        text-shadow:
            0 0 5px  #ffffff,   /* Brilho branco interno */
            0 0 15px #FFD700,   /* Brilho amarelo próximo */
            0 0 30px #FFD700,   /* Aura amarela média */
            0 0 50px #FFA500,   /* Aura laranja distante */
            0 0 80px #FF4500;   /* Aura vermelha/laranja muito distante */
        text-align: center;
        line-height: 0.9; /* Linhas mais próximas */
        transform: rotate(-3deg); /* Leve inclinação para estilo */
    }
    
    .subtitle {
        font-size: 24px;
        font-weight: 400;
        color: #ffffff;
        margin-top: 30px; /* Mais espaço do dado */
        margin-bottom: 20px;
        text-shadow: 0 2px 5px rgba(0,0,0,0.8);
        text-align: center;
    }
    
    .description {
        font-size: 16px;
        color: #e0e0e0;
        max-width: 400px;
        margin: 0 auto;
        line-height: 1.5;
    }

    /* --- BOTÃO DOURADO --- */
    .stButton > button {
        background: linear-gradient(90deg, #ff9f43, #feca57, #ff9f43);
        background-size: 200% auto;
        color: #5d2e01;
        font-weight: 800;
        font-size: 18px;
        height: 55px;
        border-radius: 50px !important;
        border: 3px solid #fff200;
        box-shadow: 0 5px 15px rgba(0,0,0,0.3);
        transition: 0.3s;
        text-transform: uppercase;
    }
    .stButton > button:hover {
        background-position: right center;
        transform: translateY(-3px) scale(1.02);
        box-shadow: 0 15px 30px rgba(255, 200, 0, 0.5);
        color: #000;
    }
    .stButton > button:active {
        color: #5d2e01;
        border-color: #fff200;
        background-color: #feca57;
        transform: translateY(-1px);
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
    
    .special-loss { 
        background-color: #ff7675; 
        color: white !important; 
        padding: 12px; 
        border-radius: 8px; 
        border: none; 
        text-align: center; 
        box-shadow: 0 2px 5px rgba(0,0,0,0.1); 
    }
    .special-guess { 
        background-color: #2ed573; 
        color: white !important; 
        padding: 12px; 
        border-radius: 8px; 
        border: none; 
        text-align: center; 
        box-shadow: 0 2px 5px rgba(0,0,0,0.1); 
    }
    
    .stSuccess { 
        text-align: center; 
        font-weight: bold; 
        font-size: 18px; 
        border-radius: 15px;
    }
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
    # --- TELA INICIAL COM NEON SCRIPT GIGANTE ---
    st.markdown("""
        <div class="welcome-box">
            <h1 class="main-title">Perfil 7</h1>
            <img src="https://img.icons8.com/3d-fluency/94/dice.png" class="golden-dice-icon">
            <div class="subtitle">Bem-vindo!</div>
            <div class="description">Clique abaixo para gerar uma nova carta com Inteligência Artificial.</div>
        </div>
    """, unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        # Botão um pouco maior e mais chamativo
        st.markdown("""
            <style>
            div[data-testid="column"] .stButton > button {
                font-size: 20px !important;
                padding: 25px 20px !important;
                height: auto !important;
            }
            </style>
        """, unsafe_allow_html=True)
        if st.button("✨ GERAR NOVA CARTA", use_container_width=True):
            with st.spinner('Sorteando...'):
                gerar_carta()
                st.rerun()

else:
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
