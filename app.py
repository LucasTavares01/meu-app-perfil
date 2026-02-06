import streamlit as st
import google.generativeai as genai
import json
import re
import traceback

# --- CONFIGURAÇÃO DE SEGURANÇA (LÓGICA BLINDADA MANTIDA) ---
try:
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
        genai.configure(api_key=api_key)
    else:
        st.error("ERRO CRÍTICO: Chave de API não encontrada nos 'Secrets'.")
        st.stop()
except Exception as e:
    st.error(f"Erro ao configurar API: {e}")
    st.stop()

# --- NOVA ESTÉTICA PREMIUM (CSS) ---
st.markdown("""
    <style>
    /* Importando fonte moderna */
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap');

    /* Fundo Geral do App */
    .stApp {
        background-color: #2c3e50;
        font-family: 'Roboto', sans-serif;
    }

    /* Container do Cartão (O "Papel") */
    .game-card {
        background-color: #ffffff;
        border-radius: 15px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.3); /* Sombra 3D */
        overflow: hidden; /* Garante que nada saia das bordas arredondadas */
        margin-bottom: 20px;
    }

    /* Cabeçalho do Cartão (Onde fica o Tema) */
    .card-header {
        background: linear-gradient(135deg, #0984e3, #74b9ff);
        color: white;
        padding: 20px;
        text-align: center;
        border-bottom: 4px solid #0652dd;
    }
    
    .header-label {
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 2px;
        opacity: 0.9;
        margin-bottom: 5px;
    }

    .theme-name {
        font-size: 28px;
        font-weight: 800;
        text-transform: uppercase;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.2);
    }

    /* Lista de Dicas */
    .hint-container {
        padding: 0;
    }

    .hint-row {
        padding: 12px 20px;
        border-bottom: 1px solid #eee;
        color: #2d3436;
        font-size: 16px;
        line-height: 1.5;
    }

    /* Efeito Zebrado (Linhas alternadas) */
    .hint-row:nth-child(even) {
        background-color: #f8f9fa;
    }

    /* Destaques Especiais (Visual Automático) */
    .special-loss {
        background-color: #ff7675 !important;
        color: white;
        font-weight: bold;
        text-align: center;
        border-left: 5px solid #d63031;
    }

    .special-guess {
        background-color: #55efc4 !important;
        color: #2d3436;
        font-weight: bold;
        text-align: center;
        border-left: 5px solid #00b894;
    }

    /* Botões Personalizados */
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 50px;
        font-weight: bold;
        font-size: 18px;
        border: none;
        transition: transform 0.1s;
    }
    
    /* Efeito de clique no botão */
    .stButton>button:active {
        transform: scale(0.98);
    }

    /* Caixa de Logs Discreta */
    .log-box {
        background-color: #000;
        color: #00ff00;
        padding: 10px;
        font-family: monospace;
        font-size: 10px;
        border-radius: 5px;
        margin-top: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- ESTADOS DA SESSÃO ---
if 'carta' not in st.session_state: st.session_state.carta = None
if 'revelado' not in st.session_state: st.session_state.revelado = False
if 'last_log' not in st.session_state: st.session_state.last_log = "Sistema visual carregado."

# --- FUNÇÃO DE AUTO-DESCOBERTA (MANTIDA IGUAL) ---
def get_best_model():
    try:
        st.session_state.last_log += "\nVerificando modelos..."
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        if any('gemini-1.5-flash' in m for m in available_models):
            chosen = next(m for m in available_models if 'gemini-1.5-flash' in m)
        elif any('gemini-2.5-flash' in m for m in available_models):
            chosen = next(m for m in available_models if 'gemini-2.5-flash' in m)
        else:
            chosen = available_models[0]
            
        st.session_state.last_log += f"\nModelo conectado: {chosen}"
        return genai.GenerativeModel(chosen)
    except Exception as e:
        st.session_state.last_log += f"\nERRO DE MODELO: {e}"
        return genai.GenerativeModel('gemini-pro')

# --- LÓGICA DE GERAÇÃO (MANTIDA IGUAL) ---
def gerar_carta():
    model = get_best_model()
    
    prompt = """
    Aja como um gerador de cartas para o jogo Perfil 7.
    
    1. TEMA OBRIGATÓRIO: O campo 'tema' deve ser EXATAMENTE um destes 5 valores: "PESSOA", "LUGAR", "ANO", "DIGITAL" ou "COISA".
    
    2. CONTEÚDO:
       - 20 dicas no total.
       - Dificuldade: 3 fáceis, 7 médias, 10 difíceis.
       - EMBARALHAMENTO: As dicas DEVEM estar em ordem aleatória de dificuldade.
       
    3. REGRAS ESPECIAIS: 
       - 30% de chance de incluir 'PERCA A VEZ' (substituindo o texto de uma dica média).
       - 30% de chance de incluir 'UM PALPITE A QUALQUER HORA' (substituindo o texto de uma dica difícil).
    
    FORMATO JSON OBRIGATÓRIO:
    {
      "tema": "PESSOA", 
      "dicas": ["1. Dica A", "2. Dica B", "3. PERCA A VEZ", ...], 
      "resposta": "RESPOSTA FINAL"
    }
    """
    try:
        response = model.generate_content(prompt)
        st.session_state.last_log += f"\n\n--- RESPOSTA BRUTA ---\n{response.text}"
        
        clean_text = response.text.replace("```json", "").replace("```", "").strip()
        match = re.search(r'\{.*\}', clean_text, re.DOTALL)
        
        if match:
            st.session_state.carta = json.loads(match.group())
            st.session_state.revelado = False
        else:
            st.session_state.last_log += "\nERRO: JSON inválido."
            st.error("Erro na leitura da carta.")
            
    except Exception as e:
        st.session_state.last_log += f"\nFALHA CRÍTICA: {traceback.format_exc()}"

# --- INTERFACE VISUAL APRIMORADA ---
st.title("🎲 Perfil 7")

if not st.session_state.carta:
    st.markdown("### Bem-vindo!")
    st.write("Clique abaixo para gerar uma nova carta com Inteligência Artificial.")
    if st.button("✨ GERAR NOVA CARTA", type="primary"):
        with st.spinner('Embaralhando e criando carta...'):
            gerar_carta()
            st.rerun()
else:
    c = st.session_state.carta
    
    # --- RENDERIZAÇÃO DO CARTÃO ---
    # Cabeçalho
    st.markdown(f"""
    <div class="game-card">
        <div class="card-header">
            <div class="header-label">DIGA AOS JOGADORES QUE SOU UM(A):</div>
            <div class="theme-name">{c.get('tema', 'TEMA')}</div>
        </div>
        <div class="hint-container">
    """, unsafe_allow_html=True)
    
    # Loop das Dicas com Estilos Inteligentes
    for dica in c.get('dicas', []):
        dica_upper = dica.upper()
        
        # Verifica se é um item especial para mudar a cor
        if "PERCA A VEZ" in dica_upper:
            st.markdown(f"<div class='hint-row special-loss'>{dica} 🚫</div>", unsafe_allow_html=True)
        elif "PALPITE A QUALQUER HORA" in dica_upper:
            st.markdown(f"<div class='hint-row special-guess'>{dica} 💡</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='hint-row'>{dica}</div>", unsafe_allow_html=True)
            
    # Fecha o Cartão
    st.markdown("</div></div>", unsafe_allow_html=True)
    
    # Botões de Ação
    col1, col2 = st.columns(2)
    with col1:
        if st.button("👁️ REVELAR RESPOSTA"): 
            st.session_state.revelado = True
    with col2:
        if st.button("🔄 NOVA CARTA"):
            st.session_state.carta = None
            st.rerun()

    if st.session_state.revelado:
        st.success(f"🏆 A RESPOSTA É: **{c.get('resposta')}**")

# Logs (Mantidos mas discretos)
st.divider()
with st.expander("🛠️ Logs do Sistema"):
    st.text(st.session_state.last_log)
