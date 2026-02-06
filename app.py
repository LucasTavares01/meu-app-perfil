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
    /* Importando fontes: Montserrat (textos) e Kaushan Script (título neon estilo referência) */
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
    .main .block-container { padding-top: 1rem; }

    /* Centralizar Spinner */
    div[data-testid="stSpinner"] {
        justify-content: center;
        color: #F3C623;
        font-weight: bold;
        margin-top: 10px;
        margin-bottom: 10px;
    }

    /* --- TELA DE BOAS-VINDAS (REFEITA IGUAL REFERÊNCIA) --- */
    .welcome-box {
        text-align: center;
        padding: 10px;
        margin-bottom: 20px;
        position: relative;
        /* Garante que o conteúdo fique centralizado */
        display: flex;
        flex-direction: column;
        align-items: center;
    }
    
    /* TÍTULO NEON (Fica atrás) */
    .main-title {
        font-family: 'Kaushan Script', cursive;
        font-size: 130px; /* Tamanho gigante */
        color: #ffffff; /* Núcleo branco */
        margin: 0;
        padding-top: 40px;
        position: relative;
        z-index: 1; /* Camada de trás */
        /* Aura neon intensa e difusa (amarelo/laranja) */
        text-shadow:
            0 0 10px #FFF,
            0 0 30px #FFD700,
            0 0 60px #FFD700,
            0 0 100px #FFD700,
            0 0 150px #FFA500;
        text-align: center;
        line-height: 0.8;
        transform: rotate(-3deg);
    }
    
    /* DADO DOURADO (Fica na frente) */
    .golden-dice-icon {
        width: 160px;
        display: block;
        /* Sombra para destacar do neon */
        filter: drop-shadow(0 5px 15px rgba(0,0,0,0.5));
        animation: floater 3s ease-in-out infinite;
        position: relative;
        z-index: 2; /* Camada da frente */
        margin-top: -90px; /* Puxa para cima para sobrepor o texto */
    }
    @keyframes floater {
        0% { transform: translateY(0px); }
        50% { transform: translateY(-10px); }
        100% { transform: translateY(0px); }
    }
    
    .subtitle {
        font-size: 24px;
        font-weight: 400;
        color: #ffffff;
        margin-top: 20px;
        margin-bottom: 20px;
        text-shadow: 0 2px 5px rgba(0,0,0,0.8);
        text-align: center;
    }

    /* --- BOTÃO DOURADO (CENTRALIZADO E TAMANHO AUTOMÁTICO) --- */
    /* CSS específico para o botão da tela inicial ficar centralizado e com largura do texto */
    .welcome-button-container .stButton {
        display: flex;
        justify-content: center;
    }

    .welcome-button-container .stButton > button {
        background: linear-gradient(90deg, #ff9f43, #feca57, #ff9f43);
        background-size: 200% auto;
        color: #5d2e01;
        font-weight: 800;
        font-size: 18px;
        /* Largura automática baseada no padding */
        width: auto !important; 
        padding: 15px 50px !important;
        height: auto !important;
        border-radius: 50px !important;
        border: 3px solid #fff200;
        box-shadow: 0 5px 15px rgba(0,0,0,0.3);
        transition: 0.3s;
        text-transform: uppercase;
        display: block;
    }
    
    .welcome-button-container .stButton > button:hover {
        background-position: right center;
        transform: translateY(-3px) scale(1.05);
        box-shadow: 0 15px 30px rgba(255, 200, 0, 0.5);
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
    
    /* Botões da tela da carta (largura total) */
    .card-screen-button .stButton > button {
        width: 100%;
        height: 50px;
        font-weight: bold;
        font-size: 16px;
    }

    .stSuccess { text-align: center; font-weight: bold; font-size: 18px; border-radius: 15px; }
    </style>
    """, unsafe_allow_html=True)

# --- ESTADOS ---
if 'carta' not in st.session_state: st.session_state.carta = None
if 'revelado' not in st.session_state: st.session_state.revelado = False

# --- FUNÇÕES (LÓGICA MANTIDA) ---
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
    # --- TELA INICIAL ---
    st.markdown("""
        <div class="welcome-box">
            <h1 class="main-title">Perfil 7</h1>
            <img src="https://img.icons8.com/3d-fluency/94/dice.png" class="golden-dice-icon">
            <div class="subtitle">Bem-vindo!</div>
        </div>
    """, unsafe_allow_html=True)
    
    # Botão Centralizado com largura automática (ajustado ao texto)
    # Usamos um container para aplicar o CSS específico
    with st.container():
        st.markdown('<div class="welcome-button-container">', unsafe_allow_html=True)
        if st.button("✨ GERAR NOVA CARTA"):
            with st.spinner('Sorteando...'):
                gerar_carta()
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

else:
    # --- TELA DA CARTA (MANTIDA PERFEITA) ---
    c = st.session_state.carta
    
    st.markdown(f"""
    <div class="card-theme-box">
        <div class="header-label">DIGA AOS JOGADORES QUE SOU UM(A):</div>
        <div class="theme-value">{c.get('tema', 'TEMA')}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Botão Revelar (Largura total, estilo padrão dos cards)
    st.markdown('<div class="card-screen-button">', unsafe_allow_html=True)
    if st.button("👁️ REVELAR RESPOSTA"): 
        st.session_state.revelado = True
    st.markdown('</div>', unsafe_allow_html=True)

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
    
    # Botão Nova Carta (Largura total)
    st.markdown('<div class="card-screen-button">', unsafe_allow_html=True)
    if st.button("🔄 NOVA CARTA"):
        st.session_state.carta = None
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
