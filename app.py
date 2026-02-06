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
        # Fallback apenas para teste local
        api_key = "COLOQUE_SUA_KEY_AQUI_SE_ESTIVER_RODANDO_LOCAL" 
        genai.configure(api_key=api_key)
except Exception:
    st.error("ERRO: Configure sua chave no painel 'Secrets' do Streamlit.")
    st.stop()

# --- ESTÉTICA "MÁGICA" (CSS) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;800&display=swap');

    /* Fundo Mágico (Roxo/Laranja/Dourado) */
    .stApp {
        background: rgb(40,15,65);
        background: linear-gradient(135deg, rgba(40,15,65,1) 0%, rgba(86,22,86,1) 30%, rgba(186,75,35,1) 65%, rgba(232,183,77,1) 100%);
        background-size: cover;
        background-attachment: fixed;
        font-family: 'Montserrat', sans-serif;
    }

    #MainMenu, footer, header {visibility: hidden;}
    .main .block-container { padding-top: 2rem; }

    /* --- TELA DE BOAS-VINDAS --- */
    .welcome-container {
        text-align: center;
        padding: 40px 20px;
        margin-top: 5vh;
    }

    .golden-dice-icon {
        width: 120px;
        margin-bottom: 25px;
        filter: drop-shadow(0 0 20px rgba(255, 215, 0, 0.7));
        animation: floater 3s ease-in-out infinite;
    }
    @keyframes floater {
        0% { transform: translateY(0px); }
        50% { transform: translateY(-10px); }
        100% { transform: translateY(0px); }
    }

    .main-title {
        font-size: 65px;
        font-weight: 800;
        color: #FFD700;
        text-transform: uppercase;
        margin-bottom: 10px;
        letter-spacing: 2px;
        text-shadow: 3px 3px 0px #c68f08, 0 0 25px rgba(255, 215, 0, 0.6);
    }

    .subtitle {
        font-size: 34px;
        font-weight: 600;
        color: #ffffff;
        margin-bottom: 15px;
        text-shadow: 0 2px 4px rgba(0,0,0,0.3);
    }

    .description {
        font-size: 18px; color: #eeeeee; max-width: 450px; margin: 0 auto 40px auto;
        line-height: 1.6; font-weight: 400;
    }

    /* --- BOTÃO DOURADO PRINCIPAL --- */
    .stButton > button {
        background: linear-gradient(90deg, #e67e22, #f1c40f, #e67e22);
        background-size: 200% auto;
        color: #4a1d03;
        font-weight: 800;
        font-size: 20px;
        padding: 18px 50px;
        border-radius: 60px !important;
        border: 2px solid #ffd000;
        box-shadow: 0 0 20px rgba(255, 200, 0, 0.6), inset 0 2px 2px rgba(255,255,255,0.4);
        transition: 0.4s;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        margin: 0 auto;
        display: block;
    }
    .stButton > button:hover {
        background-position: right center;
        transform: scale(1.05);
        box-shadow: 0 0 40px rgba(255, 215, 0, 1);
        color: #2c1302;
    }

    /* --- CARTÃO DO JOGO --- */
    .card-container {
        background-color: #ffffff;
        color: #2c3e50;
        padding: 30px;
        border-radius: 20px;
        border: 4px solid #FFD700;
        box-shadow: 0 0 30px rgba(255, 215, 0, 0.3);
        margin-top: 20px;
    }
    .header-text { font-size: 14px; color: #95a5a6; font-weight: bold; text-transform: uppercase; margin-bottom: 5px; letter-spacing: 1px;}
    .theme-title { font-size: 28px; color: #2c3e50; font-weight: 800; margin-bottom: 25px; text-transform: uppercase; border-bottom: 3px solid #FFD700; padding-bottom: 15px; }
    .hint-row { border-bottom: 1px solid #eee; padding: 14px 0; font-family: 'Montserrat', sans-serif; font-size: 16px; font-weight: 600; }
    
    /* Destaques Especiais */
    .special-loss { color: #c0392b; background-color: #fadbd8; padding-left: 15px; border-left: 6px solid #c0392b; border-radius: 8px;}
    .special-guess { color: #27ae60; background-color: #d5f5e3; padding-left: 15px; border-left: 6px solid #27ae60; border-radius: 8px;}
    
    .stSuccess { background-color: #27ae60; color: white; font-weight: bold; border: none; font-size: 18px; padding: 20px; border-radius: 15px;}

    /* Botões Secundários */
    div[data-testid="column"] .stButton > button {
        background: rgba(255,255,255,0.15);
        color: white;
        border: 2px solid rgba(255,255,255,0.5);
        box-shadow: none;
        font-size: 16px;
        padding: 12px;
        margin-top: 20px;
    }
    div[data-testid="column"] .stButton > button:hover {
        background: rgba(255,255,255,0.3);
        border-color: white;
        transform: none;
        box-shadow: 0 0 15px rgba(255,255,255,0.3);
        color: white;
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
    # --- PROMPT CORRIGIDO E MAIS RÍGIDO ---
    prompt = """
    Aja como o motor do jogo de tabuleiro 'Perfil 7'. Gere um JSON.
    
    1. TEMA: Escolha UM destes: "PESSOA", "LUGAR", "ANO", "DIGITAL" ou "COISA".
    
    2. CONTEÚDO BASE:
       - Gere 20 dicas sobre a resposta escolhida.
       - Distribuição OBRIGATÓRIA: 3 fáceis, 7 médias, 10 difíceis.
       - EMBARALHAMENTO: As dicas devem estar misturadas aleatoriamente na lista de 1 a 20.
    
    3. REGRAS DE ITENS ESPECIAIS (CRÍTICO: MÁXIMO 1 DE CADA POR CARTA):
       - Decisão 1: Existe 30% de chance de ter 'PERCA A VEZ'. Se sim, substitua APENAS UMA dica média por 'PERCA A VEZ'. (Se não, mantenha as dicas normais).
       - Decisão 2: Existe 30% de chance de ter 'UM PALPITE A QUALQUER HORA'. Se sim, substitua APENAS UMA dica difícil por 'UM PALPITE A QUALQUER HORA'.
       - NUNCA coloque mais de 1 'PERCA A VEZ' na mesma carta.
       - NUNCA coloque mais de 1 'PALPITE' na mesma carta.
    
    FORMATO JSON RETORNADO: 
    {"tema": "PESSOA", "dicas": ["1. Dica normal", "2. PERCA A VEZ", "3. Dica normal..."], "resposta": "RESPOSTA"}
    """
    try:
        response = model.generate_content(prompt)
        text = response.text.replace("```json", "").replace("```", "").strip()
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            st.session_state.carta = json.loads(match.group())
            st.session_state.revelado = False
        else:
            st.error("A IA falhou em gerar o formato correto. Tente novamente.")
    except Exception as e:
        st.error(f"Erro de conexão: {e}")

# --- INTERFACE ---
if not st.session_state.carta:
    # Tela de Boas-Vindas Mágica
    st.markdown("""
        <div class="welcome-container">
            <img src="https://cdn3d.iconscout.com/3d/premium/thumb/golden-dice-5360147-4489593.png" class="golden-dice-icon" alt="Dado Dourado">
            <div class="main-title">Perfil 7</div>
            <div class="subtitle">Bem-vindo!</div>
            <div class="description">Clique abaixo para gerar uma nova carta com Inteligência Artificial.</div>
        </div>
    """, unsafe_allow_html=True)
    
    col_l, col_main, col_r = st.columns([1, 2, 1])
    with col_main:
        if st.button("✨ GERAR NOVA CARTA"):
            with st.spinner('Invocando a sorte...'):
                gerar_carta()
                st.rerun()

else:
    c = st.session_state.carta
    # Tela da Carta
    st.markdown(f"""
    <div class="card-container">
        <div class="header-text">Diga aos jogadores que sou um(a):</div>
        <div class="theme-title">{c.get('tema', 'TEMA')}</div>
    """, unsafe_allow_html=True)
    
    for dica in c.get('dicas', []):
        dica_upper = dica.upper()
        # Tratamento visual dos itens especiais
        if "PERCA A VEZ" in dica_upper:
            st.markdown(f"<div class='hint-row special-loss'>🚫 {dica}</div>", unsafe_allow_html=True)
        elif "PALPITE" in dica_upper:
            st.markdown(f"<div class='hint-row special-guess'>💡 {dica}</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='hint-row'>{dica}</div>", unsafe_allow_html=True)
            
    st.markdown("</div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("👁️ REVELAR RESPOSTA"): st.session_state.revelado = True
    with col2:
        if st.button("🔄 NOVA CARTA"):
            st.session_state.carta = None
            st.rerun()

    if st.session_state.revelado:
        st.write("")
        st.success(f"🏆 A RESPOSTA É: {c.get('resposta')}")
