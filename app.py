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

# --- ESTÉTICA "MÁGICA" (CSS AJUSTADO PARA CENTRALIZAÇÃO) ---
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
    .main .block-container { padding-top: 3rem; }

    /* --- CENTRALIZAÇÃO GERAL --- */
    /* Força o spinner a ficar no centro */
    div[data-testid="stSpinner"] {
        justify-content: center;
        color: #FFD700;
        font-weight: bold;
    }

    /* --- TELA DE BOAS-VINDAS --- */
    .welcome-box {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        margin-bottom: 30px;
    }

    .golden-dice-icon {
        width: 140px;
        margin-bottom: 20px;
        filter: drop-shadow(0 0 25px rgba(255, 215, 0, 0.6));
        animation: floater 3s ease-in-out infinite;
        display: block;
        margin-left: auto;
        margin-right: auto;
    }
    
    @keyframes floater {
        0% { transform: translateY(0px); }
        50% { transform: translateY(-12px); }
        100% { transform: translateY(0px); }
    }

    .main-title {
        font-size: 60px;
        font-weight: 800;
        color: #FFD700;
        text-transform: uppercase;
        margin: 0;
        letter-spacing: 3px;
        text-shadow: 4px 4px 0px #8e44ad, 0 0 30px rgba(255, 215, 0, 0.5);
        text-align: center;
        line-height: 1.1;
    }

    .subtitle {
        font-size: 30px;
        font-weight: 600;
        color: #ffffff;
        margin-top: 10px;
        margin-bottom: 10px;
        text-shadow: 0 2px 5px rgba(0,0,0,0.5);
        text-align: center;
    }

    .description {
        font-size: 16px; color: #e0e0e0; max-width: 500px; margin: 10px auto 40px auto;
        line-height: 1.5; font-weight: 400; text-align: center;
    }

    /* --- BOTÃO DOURADO PRINCIPAL --- */
    .stButton > button {
        background: linear-gradient(90deg, #ff9f43, #feca57, #ff9f43);
        background-size: 200% auto;
        color: #5d2e01;
        font-weight: 800;
        font-size: 20px;
        padding: 0px 40px;
        height: 60px;
        border-radius: 50px !important;
        border: 3px solid #fff200;
        box-shadow: 0 10px 20px rgba(0,0,0,0.2), inset 0 2px 0 rgba(255,255,255,0.4);
        transition: 0.4s;
        text-transform: uppercase;
        width: 100%; /* Ocupa a coluna inteira */
    }
    .stButton > button:hover {
        background-position: right center;
        transform: translateY(-3px);
        box-shadow: 0 15px 30px rgba(255, 200, 0, 0.4);
        color: #000;
    }

    /* --- DESIGN DA CARTA (Separação Elegante) --- */
    
    /* 1. Bloco do TEMA (Topo) */
    .card-theme-box {
        background: #ffffff;
        padding: 25px;
        border-radius: 20px;
        text-align: center;
        border: 4px solid #FFD700;
        box-shadow: 0 10px 25px rgba(0,0,0,0.3);
        margin-bottom: 20px; /* Espaço para o botão respirar */
    }
    
    /* 2. Bloco das DICAS (Corpo) */
    .card-tips-box {
        background: #ffffff;
        padding: 10px 20px 30px 20px;
        border-radius: 20px;
        border: 4px solid #FFD700;
        box-shadow: 0 10px 25px rgba(0,0,0,0.3);
    }

    .header-label { font-size: 13px; color: #95a5a6; font-weight: 700; text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 5px;}
    .theme-value { font-size: 36px; color: #2c3e50; font-weight: 900; text-transform: uppercase; margin: 0; line-height: 1; }

    .hint-row { border-bottom: 1px solid #f1f2f6; padding: 15px 5px; font-family: 'Montserrat', sans-serif; font-size: 16px; font-weight: 600; color: #2f3542; }
    
    /* Destaques */
    .special-loss { background-color: #ff7675; color: white; padding: 15px; border-radius: 10px; border: none; text-align: center; box-shadow: 0 4px 10px rgba(214, 48, 49, 0.2); }
    .special-guess { background-color: #2ed573; color: white; padding: 15px; border-radius: 10px; border: none; text-align: center; box-shadow: 0 4px 10px rgba(46, 213, 115, 0.2); }
    
    /* Resposta Final */
    .stSuccess { background-color: #2ecc71; color: white; font-weight: bold; border: none; font-size: 20px; padding: 20px; border-radius: 15px; text-align: center; }

    /* Ajuste de Botões Secundários */
    div[data-testid="column"] button {
        font-size: 16px !important;
        height: 50px !important;
    }

    </style>
    """, unsafe_allow_html=True)

# --- ESTADOS ---
if 'carta' not in st.session_state: st.session_state.carta = None
if 'revelado' not in st.session_state: st.session_state.revelado = False

# --- LÓGICA (MANTIDA) ---
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
    Aja como o motor do jogo 'Perfil 7'. Gere JSON.
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
    # TELA INICIAL (USANDO HTML PURO PARA CENTRALIZAR O TEXTO)
    st.markdown("""
        <div class="welcome-box">
            <img src="https://img.icons8.com/3d-fluency/94/dice.png" class="golden-dice-icon">
            <h1 class="main-title">PERFIL 7</h1>
            <div class="subtitle">Bem-vindo!</div>
            <div class="description">Clique abaixo para gerar uma nova carta com Inteligência Artificial.</div>
        </div>
    """, unsafe_allow_html=True)
    
    # CENTRALIZAÇÃO DO BOTÃO VIA COLUNAS
    # Usando proporção 1:2:1 para garantir que o botão fique no meio
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        if st.button("✨ GERAR NOVA CARTA"):
            with st.spinner('Sorteando...'):
                gerar_carta()
                st.rerun()

else:
    c = st.session_state.carta
    
    # 1. CARTÃO DE TEMA (Separado para não cortar o botão)
    st.markdown(f"""
    <div class="card-theme-box">
        <div class="header-label">DIGA AOS JOGADORES QUE SOU UM(A):</div>
        <div class="theme-value">{c.get('tema', 'TEMA')}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # 2. BOTÃO REVELAR (Centralizado entre os cards)
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        if st.button("👁️ REVELAR RESPOSTA"): 
            st.session_state.revelado = True

    if st.session_state.revelado:
        st.success(f"🏆 {c.get('resposta')}")
        st.markdown("<br>", unsafe_allow_html=True) # Espacinho

    # 3. CARTÃO DE DICAS (Lista limpa)
    st.markdown('<div class="card-tips-box">', unsafe_allow_html=True)
    for dica in c.get('dicas', []):
        d_up = dica.upper()
        if "PERCA A VEZ" in d_up:
            st.markdown(f"<div class='hint-row special-loss'>🚫 {dica}</div>", unsafe_allow_html=True)
        elif "PALPITE" in d_up:
            st.markdown(f"<div class='hint-row special-guess'>💡 {dica}</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='hint-row'>{dica}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    
    # 4. BOTÃO VOLTAR
    st.write("")
    if st.button("🔄 NOVA CARTA"):
        st.session_state.carta = None
        st.rerun()
