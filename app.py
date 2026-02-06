import streamlit as st
import google.generativeai as genai
import json
import re
import traceback

# --- CONFIGURAÇÃO SEGURA ---
# Agora o app pega a chave do "Cofre" do Streamlit
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
except Exception:
    st.error("ERRO: Você esqueceu de configurar a 'Secret' no painel do Streamlit com a nova chave.")
    st.stop()

# Estilização Visual
st.markdown("""
    <style>
    .stApp { background-color: #1e272e; color: white; }
    .card-container { background-color: #d1d8e0; color: #2f3640; padding: 25px; border-radius: 5px; border-left: 15px solid #0984e3; }
    .hint-line { border-bottom: 1px solid #7f8c8d; padding: 8px 0; font-family: sans-serif; font-size: 16px; font-weight: bold; }
    .header-text { color: #2f3640; font-weight: bold; margin-bottom: 15px; text-transform: uppercase; border-bottom: 2px solid #2f3640; font-size: 18px; }
    .stButton>button { width: 100%; background-color: #0984e3; color: white; border: none; padding: 15px; font-weight: bold; font-size: 16px; }
    .log-box { background-color: #000; color: #0f0; padding: 10px; font-family: monospace; font-size: 11px; border-radius: 5px; overflow-x: auto; margin-top: 20px; }
    </style>
    """, unsafe_allow_html=True)

if 'carta' not in st.session_state: st.session_state.carta = None
if 'revelado' not in st.session_state: st.session_state.revelado = False
if 'last_log' not in st.session_state: st.session_state.last_log = "Sistema reiniciado com nova chave segura..."

# --- FUNÇÃO DE AUTO-DESCOBERTA DE MODELO ---
def get_best_model():
    try:
        st.session_state.last_log += "\nBuscando modelos..."
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # Prioridade para modelos Flash (mais rápidos)
        if any('gemini-1.5-flash' in m for m in available_models):
            chosen = next(m for m in available_models if 'gemini-1.5-flash' in m)
        elif any('gemini-2.5-flash' in m for m in available_models):
            chosen = next(m for m in available_models if 'gemini-2.5-flash' in m)
        else:
            chosen = available_models[0]
            
        st.session_state.last_log += f"\nConectado ao modelo: {chosen}"
        return genai.GenerativeModel(chosen)
    except Exception as e:
        st.session_state.last_log += f"\nERRO DE CONEXÃO: {e}"
        return genai.GenerativeModel('gemini-pro')

def gerar_carta():
    model = get_best_model()
    prompt = """
    Gere um JSON para o jogo Perfil 7.
    Tema: Ano, Pessoa, Lugar, Digital ou Coisa.
    20 dicas (3 fáceis, 7 médias, 10 difíceis) em ORDEM ALEATÓRIA.
    Especiais: 30% chance de 'PERCA A VEZ', 30% 'PALPITE A QUALQUER HORA'.
    JSON PURO: {"tema": "...", "dicas": ["..."], "resposta": "..."}
    """
    try:
        response = model.generate_content(prompt)
        
        # Limpeza robusta para garantir JSON
        clean_text = response.text.replace("```json", "").replace("```", "")
        match = re.search(r'\{.*\}', clean_text, re.DOTALL)
        
        if match:
            st.session_state.carta = json.loads(match.group())
            st.session_state.revelado = False
        else:
            st.session_state.last_log += f"\nERRO: IA não enviou JSON válido.\n{response.text}"
            st.error("Erro na leitura. Tente de novo.")
    except Exception as e:
        st.session_state.last_log += f"\nFALHA: {traceback.format_exc()}"

# --- INTERFACE ---
st.title("🃏 Perfil 7 AI")

if not st.session_state.carta:
    if st.button("✨ GERAR NOVA CARTA"):
        with st.spinner('Gerando carta com chave segura...'):
            gerar_carta()
            st.rerun()
else:
    c = st.session_state.carta
    st.markdown(f'<div class="card-container"><div class="header-text">Sou um(a): {c.get("tema", "???")}</div>', unsafe_allow_html=True)
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
with st.expander("🛠️ Logs"):
    st.text(st.session_state.last_log)
