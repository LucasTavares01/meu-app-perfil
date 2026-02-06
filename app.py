import streamlit as st
import google.generativeai as genai
import json
import re
import traceback

# --- CONFIGURAÇÃO DE SEGURANÇA (MANTIDA IGUAL) ---
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

# --- ESTILIZAÇÃO VISUAL (MANTIDA IGUAL) ---
st.markdown("""
    <style>
    .stApp { background-color: #1e272e; color: white; }
    .card-container { background-color: #ecf0f1; color: #2c3e50; padding: 25px; border-radius: 8px; border-left: 15px solid #0984e3; }
    .header-text { font-size: 14px; color: #7f8c8d; font-weight: bold; text-transform: uppercase; margin-bottom: 5px; }
    .theme-title { font-size: 22px; color: #2c3e50; font-weight: 800; margin-bottom: 20px; text-transform: uppercase; border-bottom: 2px solid #bdc3c7; padding-bottom: 10px; }
    .hint-line { border-bottom: 1px solid #bdc3c7; padding: 8px 0; font-family: sans-serif; font-size: 15px; font-weight: bold; }
    .stButton>button { width: 100%; background-color: #0984e3; color: white; border: none; padding: 15px; font-weight: bold; font-size: 16px; margin-top: 10px; }
    .stButton>button:hover { background-color: #74b9ff; }
    .log-box { background-color: #000; color: #0f0; padding: 10px; font-family: monospace; font-size: 11px; border-radius: 5px; overflow-x: auto; margin-top: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- ESTADOS DA SESSÃO ---
if 'carta' not in st.session_state: st.session_state.carta = None
if 'revelado' not in st.session_state: st.session_state.revelado = False
if 'last_log' not in st.session_state: st.session_state.last_log = "Sistema iniciado."

# --- FUNÇÃO DE AUTO-DESCOBERTA DE MODELO ---
def get_best_model():
    try:
        st.session_state.last_log += "\nBuscando modelos disponíveis..."
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        if any('gemini-1.5-flash' in m for m in available_models):
            chosen = next(m for m in available_models if 'gemini-1.5-flash' in m)
        elif any('gemini-2.5-flash' in m for m in available_models):
            chosen = next(m for m in available_models if 'gemini-2.5-flash' in m)
        else:
            chosen = available_models[0]
            
        st.session_state.last_log += f"\nConectado ao modelo: {chosen}"
        return genai.GenerativeModel(chosen)
    except Exception as e:
        st.session_state.last_log += f"\nERRO AO BUSCAR MODELOS: {e}"
        return genai.GenerativeModel('gemini-pro')

def gerar_carta():
    model = get_best_model()
    
    # --- AQUI ESTÁ A ÚNICA ALTERAÇÃO: PROMPT MAIS RÍGIDO NOS TEMAS ---
    prompt = """
    Aja como um gerador de cartas para o jogo Perfil 7.
    
    1. TEMA OBRIGATÓRIO: O campo 'tema' deve ser EXATAMENTE um destes 5 valores: "PESSOA", "LUGAR", "ANO", "DIGITAL" ou "COISA". Não use "Personalidade", "Objeto" ou qualquer outro sinônimo.
    
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
        st.session_state.last_log += f"\n\n--- RESPOSTA DA IA ---\n{response.text}"
        
        clean_text = response.text.replace("```json", "").replace("```", "").strip()
        match = re.search(r'\{.*\}', clean_text, re.DOTALL)
        
        if match:
            st.session_state.carta = json.loads(match.group())
            st.session_state.revelado = False
        else:
            st.session_state.last_log += "\nERRO: JSON não encontrado na resposta."
            st.error("Erro na leitura da carta. Veja os logs abaixo.")
            
    except Exception as e:
        st.session_state.last_log += f"\nERRO CRÍTICO NA GERAÇÃO: {traceback.format_exc()}"

# --- INTERFACE (MANTIDA IGUAL) ---
st.title("🃏 Perfil 7 AI")

if not st.session_state.carta:
    if st.button("✨ GERAR NOVA CARTA"):
        with st.spinner('Gerando carta...'):
            gerar_carta()
            st.rerun()
else:
    c = st.session_state.carta
    st.markdown(f"""
    <div class="card-container">
        <div class="header-text">Diga aos jogadores que sou um(a):</div>
        <div class="theme-title">{c.get('tema', 'TEMA')}</div>
    """, unsafe_allow_html=True)
    
    for dica in c.get('dicas', []):
        st.markdown(f"<div class='hint-line'>{dica}</div>", unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔍 REVELAR"): st.session_state.revelado = True
    with col2:
        if st.button("🔄 NOVA CARTA"):
            st.session_state.carta = None
            st.rerun()

    if st.session_state.revelado:
        st.success(f"RESPOSTA: {c.get('resposta')}")

st.divider()
with st.expander("🛠️ Logs Técnicos (Clique aqui se não funcionar)"):
    st.text(st.session_state.last_log)
