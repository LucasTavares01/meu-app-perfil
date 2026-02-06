import streamlit as st
import google.generativeai as genai
import random
import json

# Configuração da sua API
# Substitua pela sua chave se necessário, mas usei a que você forneceu
genai.configure(api_key="AIzaSyBdiuvsktRme3A2k-HhkoQZU211mP76oV8")

# Usando o modelo Flash que é mais estável e rápido para o plano gratuito
model = genai.GenerativeModel('gemini-1.5-flash')

# Estilização Visual inspirada no Perfil 7
st.markdown("""
    <style>
    .stApp { background-color: #1e272e; color: white; }
    .card-container { background-color: #d1d8e0; color: #2f3640; padding: 25px; border-radius: 5px; border-left: 15px solid #0984e3; box-shadow: 10px 10px 5px 0px rgba(0,0,0,0.75); }
    .hint-line { border-bottom: 1px solid #7f8c8d; padding: 8px 0; font-family: 'Arial', sans-serif; font-size: 16px; font-weight: bold; }
    .header-text { color: #2f3640; font-weight: bold; margin-bottom: 15px; text-transform: uppercase; border-bottom: 2px solid #2f3640; }
    .stButton>button { width: 100%; background-color: #0984e3; color: white; border: none; padding: 15px; font-weight: bold; }
    .stButton>button:hover { background-color: #74b9ff; color: white; }
    </style>
    """, unsafe_allow_html=True)

if 'carta' not in st.session_state:
    st.session_state.carta = None
    st.session_state.revelado = False

def gerar_carta():
    # Prompt detalhado para garantir as regras de dificuldade e aleatoriedade
    prompt = """
    Gere uma carta de Perfil 7 em formato JSON rigoroso.
    Temas possíveis: Ano, Pessoa, Lugar, Digital ou Coisa.
    Instruções:
    1. Escolha uma resposta secreta e 20 dicas únicas.
    2. Níveis: 3 fáceis, 7 médias e 10 difíceis.
    3. EMBARALHAMENTO: Distribua as dificuldades de forma TOTALMENTE ALEATÓRIA entre os números 1 e 20.
    4. ITENS ESPECIAIS (OPCIONAIS): 
       - 30% de chance de uma dica média ser trocada por 'PERCA A VEZ'.
       - 30% de chance de uma dica difícil ser trocada por 'UM PALPITE A QUALQUER HORA'.
    Retorne APENAS o JSON no formato:
    {"tema": "NOME DO TEMA", "dicas": ["1. Dica", "2. Dica"...], "resposta": "RESPOSTA"}
    """
    try:
        response = model.generate_content(prompt)
        # Limpeza para garantir que venha apenas o JSON
        txt = response.text.replace('```json', '').replace('```', '').strip()
        st.session_state.carta = json.loads(txt)
        st.session_state.revelado = False
    except Exception as e:
        st.error(f"Erro ao gerar carta: {e}")

# Interface Principal
st.title("🃏 Perfil 7 - AI Edition")

if not st.session_state.carta:
    st.markdown("<br><br>", unsafe_allow_html=True)
    if st.button("✨ GERAR NOVA CARTA"):
        with st.spinner('A IA está preparando sua carta...'):
            gerar_carta()
            st.rerun()
else:
    c = st.session_state.carta
    
    # Visual da Carta
    st.markdown(f"""
    <div class="card-container">
        <div class="header-text">Diga aos jogadores que sou um(a): {c['tema']}</div>
    """, unsafe_allow_html=True)
    
    for dica in c['dicas']:
        st.markdown(f"<div class='hint-line'>{dica}</div>", unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Botões de Ação
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔍 REVELAR RESPOSTA"):
            st.session_state.revelado = True
    
    with col2:
        if st.button("🔄 NOVA CARTA"):
            st.session_state.carta = None
            st.session_state.revelado = False
            st.rerun()

    if st.session_state.revelado:
        st.info(f"💡 A RESPOSTA É: **{c['resposta']}**")
