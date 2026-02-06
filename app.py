import streamlit as st
import google.generativeai as genai
import json
import re
import traceback

# --- CONFIGURAÇÃO DE SEGURANÇA ---
# Tenta pegar do cofre (Secrets). Se não achar, avisa o usuário.
try:
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
    else:
        # Fallback apenas para teste local (não recomendado para produção)
        api_key = "COLOQUE_SUA_KEY_AQUI_SE_ESTIVER_RODANDO_LOCAL" 
        
    genai.configure(api_key=api_key)
except Exception:
    st.error("ERRO: Configure sua chave no painel 'Secrets' do Streamlit.")
    st.stop()

# --- ESTILIZAÇÃO VISUAL ---
st.markdown("""
    <style>
    .stApp { background-color: #1e272e; color: white; }
    .card-container { background-color: #ecf0f1; color: #2c3e50; padding: 20px; border-radius: 8px; border-left: 12px solid #3498db; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }
    .header-text { font-size: 14px; color: #7f8c8d; font-weight: bold; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px; }
    .theme-title { font-size: 24px; color: #2c3e50; font-weight: 800; margin-bottom: 20px; text-transform: uppercase; border-bottom: 2px solid #bdc3c7; padding-bottom: 10px; }
    .hint-row { border-bottom: 1px solid #bdc3c7; padding: 8px 0; font-family: 'Helvetica', sans-serif; font-size: 15px; line-height: 1.4; }
    /* Destaque para itens especiais */
    .special-loss { color: #e74c3c; font-weight: bold; text-align: center; background-color: #fadbd8; padding: 5px; border-radius: 4px; }
    .special-guess { color: #27ae60; font-weight: bold; text-align: center; background-color: #d5f5e3; padding: 5px; border-radius: 4px; }
    .stButton>button { width: 100%; background-color: #2980b9; color: white; border: none; padding: 12px; font-weight: bold; border-radius: 6px; margin-top: 10px; }
    .stButton>button:hover { background-color: #3498db; }
    </style>
    """, unsafe_allow_html=True)

# --- ESTADOS ---
if 'carta' not in st.session_state: st.session_state.carta = None
if 'revelado' not in st.session_state: st.session_state.revelado = False

# --- FUNÇÃO GERADORA ---
def get_model():
    # Tenta usar modelos mais novos primeiro
    models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    if any('gemini-1.5-flash' in m for m in models): return genai.GenerativeModel('gemini-1.5-flash')
    if any('gemini-2.0-flash' in m for m in models): return genai.GenerativeModel('gemini-2.0-flash')
    return genai.GenerativeModel('gemini-pro')

def gerar_carta():
    model = get_model()
    
    # PROMPT RIGOROSO PARA FORMATAÇÃO PERFEITA
    prompt = """
    Você é um motor de jogo para 'Perfil 7'. Gere um JSON rigoroso.
    
    1. ESCOLHA UM TEMA: Ano, Pessoa, Lugar, Digital ou Coisa.
    2. GERE 20 DICAS:
       - 3 Fáceis, 7 Médias, 10 Difíceis.
       - IMPORTANTÍSSIMO: Embaralhe a ordem das dificuldades. A dica 1 não pode ser sempre fácil. Misture tudo entre 1 e 20.
    
    3. REGRAS DE SUBSTITUIÇÃO (ITENS ESPECIAIS):
       - Role um dado virtual. 30% de chance de ativar 'PERCA A VEZ'. Se ativar, ESCOLHA UMA DICA MÉDIA E APAGUE O TEXTO DELA, substituindo APENAS por: "PERCA A VEZ".
       - Role um dado virtual. 30% de chance de ativar 'PALPITE A QUALQUER HORA'. Se ativar, ESCOLHA UMA DICA DIFÍCIL E APAGUE O TEXTO DELA, substituindo APENAS por: "UM PALPITE A QUALQUER HORA".
    
    4. FORMATO DE SAÍDA (Obrigatório):
       - Não use parênteses com a dificuldade (ex: não escreva "(difícil)").
       - Numere as dicas de "1." a "20.".
       
    JSON ESPERADO:
    {
      "tema": "NOME DO TEMA EM MAIÚSCULO",
      "dicas": [
        "1. Texto da primeira dica aqui",
        "2. Texto da segunda dica aqui",
        "3. PERCA A VEZ",
        "4. Texto da quarta dica aqui..."
      ],
      "resposta": "RESPOSTA EXATA"
    }
    """
    
    try:
        response = model.generate_content(prompt)
        text = response.text.replace("```json", "").replace("```", "")
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            st.session_state.carta = json.loads(match.group())
            st.session_state.revelado = False
        else:
            st.error("Erro de leitura da IA. Tente novamente.")
    except Exception as e:
        st.error(f"Erro de conexão: {e}")

# --- INTERFACE ---
st.title("🃏 Perfil 7 AI")

if not st.session_state.carta:
    if st.button("✨ GERAR NOVA CARTA"):
        with st.spinner('Criando carta...'):
            gerar_carta()
            st.rerun()
else:
    c = st.session_state.carta
    
    # Renderização Visual da Carta
    st.markdown(f"""
    <div class="card-container">
        <div class="header-text">Diga aos jogadores que sou um(a):</div>
        <div class="theme-title">{c.get('tema', 'TEMA')}</div>
    """, unsafe_allow_html=True)
    
    # Loop inteligente para formatar as linhas especiais
    for dica in c.get('dicas', []):
        if "PERCA A VEZ" in dica.upper():
            st.markdown(f"<div class='hint-row special-loss'>{dica}</div>", unsafe_allow_html=True)
        elif "PALPITE" in dica.upper():
            st.markdown(f"<div class='hint-row special-guess'>{dica}</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='hint-row'>{dica}</div>", unsafe_allow_html=True)
            
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
