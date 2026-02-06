import streamlit as st
import google.generativeai as genai
import json
import re
import traceback

# --- CONFIGURAÇÃO DE SEGURANÇA (LÓGICA MANTIDA) ---
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

# --- NOVA ESTÉTICA "MÁGICA" (CSS) ---
st.markdown("""
    <style>
    /* Importando fontes modernas */
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;800&display=swap');

    /* --- FUNDO GLOBAL DO APP --- */
    /* Simulação do fundo de nuvens coloridas usando gradiente CSS complexo */
    .stApp {
        background: rgb(40,15,65);
        background: linear-gradient(135deg, rgba(40,15,65,1) 0%, rgba(86,22,86,1) 30%, rgba(186,75,35,1) 65%, rgba(232,183,77,1) 100%);
        background-size: cover;
        background-attachment: fixed;
        font-family: 'Montserrat', sans-serif;
    }

    /* Esconde elementos padrões do Streamlit para limpar a tela */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Remove padding padrão do topo */
    .main .block-container {
        padding-top: 2rem;
    }

    /* --- TELA INICIAL (BEM-VINDO) --- */
    .welcome-container {
        text-align: center;
        padding: 40px 20px;
        margin-top: 5vh;
    }

    .golden-dice-icon {
        width: 120px;
        margin-bottom: 25px;
        /* Efeito de brilho dourado intenso no ícone */
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
        color: #FFD700; /* Dourado */
        text-transform: uppercase;
        margin-bottom: 10px;
        letter-spacing: 2px;
        /* Sombra 3D forte */
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
        font-size: 18px;
        color: #eeeeee;
        max-width: 450px;
        margin: 0 auto 40px auto;
        line-height: 1.6;
        font-weight: 400;
    }

    /* --- ESTILO DO BOTÃO PRINCIPAL (TELA INICIAL) --- */
    /* Usamos um seletor específico para pegar o botão solto na tela inicial */
    .stButton > button {
        background: linear-gradient(90deg, #e67e22, #f1c40f, #e67e22); /* Gradiente Dourado/Laranja */
        background-size: 200% auto;
        color: #4a1d03; /* Texto marrom escuro para contraste no dourado */
        font-weight: 800;
        font-size: 20px;
        padding: 18px 50px;
        border-radius: 60px !important; /* Bordas redondas */
        border: 2px solid #ffd000;
        box-shadow: 0 0 20px rgba(255, 200, 0, 0.6), inset 0 2px 2px rgba(255,255,255,0.4);
        transition: 0.4s;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        margin: 0 auto;
        display: block;
    }

    .stButton > button:hover {
        background-position: right center; /* Anima o gradiente */
        transform: scale(1.05);
        box-shadow: 0 0 40px rgba(255, 215, 0, 1);
        color: #2c1302;
    }

    /* --- ESTILO DA CARTA (QUANDO GERADA) --- */
    /* Adaptado para o fundo escuro */
    .card-container {
        background-color: #ffffff;
        color: #2c3e50;
        padding: 30px;
        border-radius: 20px;
        /* Borda dourada brilhante */
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
    
    /* Mensagem de Sucesso (Resposta) */
    .stSuccess { background-color: #27ae60; color: white; font-weight: bold; border: none; font-size: 18px; padding: 20px; border-radius: 15px;}

    /* Botões secundários da tela da carta (para não ficarem iguais ao douradão) */
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
    Aja como um gerador de cartas para o jogo Perfil 7.
    1. TEMA OBRIGATÓRIO: EXATAMENTE um destes: "PESSOA", "LUGAR", "ANO", "DIGITAL" ou "COISA".
    2. CONTEÚDO: 20 dicas (3 fáceis, 7 médias, 10 difíceis) em ORDEM ALEATÓRIA de dificuldade.
    3. REGRAS ESPECIAIS: 
       - 30% chance 'PERCA A VEZ' (substitui texto de dica média).
       - 30% chance 'UM PALPITE A QUALQUER HORA' (substitui texto de dica difícil).
    FORMATO JSON: {"tema": "PESSOA", "dicas": ["1. Dica", "2. PERCA A VEZ", ...], "resposta": "RESPOSTA"}
    """
    try:
        response = model.generate_content(prompt)
        text = response.text.replace("```json", "").replace("```", "").strip()
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            st.session_state.carta = json.loads(match.group())
            st.session_state.revelado = False
        else:
            st.error("Erro na IA. Tente novamente.")
    except Exception as e:
        st.error(f"Erro de conexão: {e}")

# --- INTERFACE PRINCIPAL ---

# SE NÃO TEM CARTA GERADA -> MOSTRA A TELA DE BOAS-VINDAS MÁGICA
if not st.session_state.carta:
    # Usei uma URL pública de um ícone de dado dourado 3D que encontrei
    st.markdown("""
        <div class="welcome-container">
            <img src="https://cdn3d.iconscout.com/3d/premium/thumb/golden-dice-5360147-4489593.png" class="golden-dice-icon" alt="Dado Dourado">
            <div class="main-title">Perfil 7</div>
            <div class="subtitle">Bem-vindo!</div>
            <div class="description">Clique abaixo para gerar uma nova carta com Inteligência Artificial.</div>
        </div>
    """, unsafe_allow_html=True)
    
    # Botão centralizado (estilizado pelo CSS para ser dourado e redondo)
    # Usando colunas vazias nas laterais para forçar a centralização do botão
    col_l, col_main, col_r = st.columns([1, 2, 1])
    with col_main:
        if st.button("✨ GERAR NOVA CARTA"):
            with st.spinner('Invocando a sorte...'):
                gerar_carta()
                st.rerun()

# SE TEM CARTA -> MOSTRA A CARTA (Visual adaptado para o fundo escuro)
else:
    c = st.session_state.carta
    
    st.markdown(f"""
    <div class="card-container">
        <div class="header-text">Diga aos jogadores que sou um(a):</div>
        <div class="theme-title">{c.get('tema', 'TEMA')}</div>
    """, unsafe_allow_html=True)
    
    for dica in c.get('dicas', []):
        dica_upper = dica.upper()
        if "PERCA A VEZ" in dica_upper:
            st.markdown(f"<div class='hint-row special-loss'>🚫 {dica}</div>", unsafe_allow_html=True)
        elif "PALPITE" in dica_upper:
            st.markdown(f"<div class='hint-row special-guess'>💡 {dica}</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='hint-row'>{dica}</div>", unsafe_allow_html=True)
            
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Botões de Ação (Estilo secundário transparente)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("👁️ REVELAR RESPOSTA"): st.session_state.revelado = True
    with col2:
        if st.button("🔄 NOVA CARTA"):
            st.session_state.carta = None
            st.rerun()

    if st.session_state.revelado:
        st.write("") # Espaço
        st.success(f"🏆 A RESPOSTA É: {c.get('resposta')}")
