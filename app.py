import streamlit as st
from groq import Groq
import json
import re
import traceback
import time
import random
import difflib

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Perfil 7 AI",
    page_icon="🎲",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- CONFIGURAÇÃO DE SEGURANÇA (GROQ) ---
try:
    if "GROQ_API_KEY" in st.secrets:
        api_key = st.secrets["GROQ_API_KEY"]
    else:
        api_key = "teste" 
    
    if api_key == "teste" and "GROQ_API_KEY" not in st.secrets:
        st.warning("⚠️ Chave de API não detectada. Configure 'GROQ_API_KEY' nos Secrets.")
        
    client = Groq(api_key=api_key)
except Exception:
    st.error("ERRO CRÍTICO: Falha ao inicializar cliente Groq.")
    st.stop()

# --- CSS RESPONSIVO ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;800&display=swap');

    .stApp {
        background: rgb(40,15,65);
        background: linear-gradient(135deg, rgba(40,15,65,1) 0%, rgba(86,22,86,1) 30%, rgba(186,75,35,1) 65%, rgba(232,183,77,1) 100%);
        background-size: cover;
        background-attachment: fixed;
        font-family: 'Montserrat', sans-serif;
    }

    #MainMenu, footer, header {visibility: hidden;}
    
    .main .block-container { 
        padding-top: 2rem; 
        padding-left: 1rem;
        padding-right: 1rem;
    }

    .main-title {
        font-size: clamp(45px, 12vw, 90px) !important; 
        font-weight: 800;
        color: #F3C623;
        margin: 0;
        text-shadow: 0 0 15px rgba(243, 198, 35, 0.6);
        text-align: center;
        line-height: 1.1;
    }
    
    .subtitle {
        font-size: clamp(18px, 5vw, 26px);
        font-weight: 400;
        color: #ffffff;
        margin-bottom: 20px;
        text-align: center;
    }

    .golden-dice-icon {
        width: clamp(80px, 20vw, 130px);
        display: block;
        margin: 20px auto 10px auto;
        filter: drop-shadow(0 0 20px rgba(243, 198, 35, 0.5));
        animation: floater 3s ease-in-out infinite;
    }

    @keyframes floater {
        0% { transform: translateY(0px); }
        50% { transform: translateY(-10px); }
        100% { transform: translateY(0px); }
    }

    .card-theme-box {
        background: #ffffff;
        padding: 15px;
        border-radius: 15px;
        text-align: center;
        border: 4px solid #FFD700;
        box-shadow: 0 10px 20px rgba(0,0,0,0.3);
        margin-bottom: 15px;
    }
    .theme-value { 
        font-size: clamp(24px, 7vw, 32px); 
        color: #2c3e50; 
        font-weight: 900; 
        text-transform: uppercase; 
    }

    .card-tips-box {
        background: #ffffff;
        padding: 5px 15px;
        border-radius: 15px;
        border: 4px solid #FFD700;
        box-shadow: 0 10px 20px rgba(0,0,0,0.3);
        margin-top: 15px;
    }

    .hint-row { 
        border-bottom: 1px solid #e0e0e0; 
        padding: clamp(8px, 3vw, 12px) 0; 
        font-size: clamp(14px, 4vw, 16px); 
        font-weight: 700; 
        color: #1e272e; 
    }

    .stButton > button {
        background: linear-gradient(90deg, #ff9f43, #feca57, #ff9f43);
        color: #5d2e01;
        font-weight: 800;
        border-radius: 50px !important;
        border: 3px solid #fff200;
        transition: 0.3s;
    }

    @media (max-width: 640px) {
        div[data-testid="column"] {
            width: 100% !important;
            min-width: 100% !important;
        }
    }

    .log-text { font-family: monospace; font-size: 11px; color: #00ff00; background: black; padding: 5px; }
    </style>
    """, unsafe_allow_html=True)

# --- ESTADOS E LOGS ---
if 'carta' not in st.session_state: st.session_state.carta = None
if 'reserva' not in st.session_state: st.session_state.reserva = None
if 'revelado' not in st.session_state: st.session_state.revelado = False
if 'logs' not in st.session_state: st.session_state.logs = []
if 'used_answers' not in st.session_state: st.session_state.used_answers = [] 

def registrar_log(msg):
    timestamp = time.strftime("%H:%M:%S")
    st.session_state.logs.append(f"[{timestamp}] {msg}")

# --- FUNÇÃO DE BLINDAGEM (CORREÇÃO DO ERRO 'DICT') ---
def sanitizar_item(item):
    """Garante que o item seja uma string limpa, mesmo se vier como dict"""
    if isinstance(item, str):
        return item.strip()
    elif isinstance(item, dict):
        # Se vier {'dica': 'texto'}, pega o primeiro valor
        try:
            return str(list(item.values())[0]).strip()
        except:
            return str(item)
    elif item is None:
        return ""
    else:
        return str(item)

def verificar_similaridade(nova_resposta):
    nova = sanitizar_item(nova_resposta).lower()
    for usada in st.session_state.used_answers:
        usada_clean = sanitizar_item(usada).lower()
        if nova in usada_clean or usada_clean in nova:
            return True
        if difflib.SequenceMatcher(None, nova, usada_clean).ratio() > 0.8:
            return True
    return False

# --- FUNÇÕES DE GERAÇÃO ---

def gerar_dicas_complementares(resposta, quantidade_necessaria, tema):
    prompt_rescue = f"""
    Estou criando um jogo sobre: {resposta} (Tema: {tema}).
    Preciso de {quantidade_necessaria} fatos NOVOS e VERDADEIROS sobre isso.
    REGRAS: Resposta "{resposta}" PROIBIDA no texto. Retorne JSON: {{"dicas_extras": []}}
    """
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt_rescue}],
            temperature=0.2,
            response_format={"type": "json_object"}
        )
        raw_list = json.loads(completion.choices[0].message.content).get("dicas_extras", [])
        # Sanitiza a saída da IA
        return [sanitizar_item(x) for x in raw_list]
    except: return []

def auditar_dicas_ano(ano_alvo, lista_dicas_candidatas):
    prompt_auditoria = f"""Ano alvo: {ano_alvo}. Retorne apenas dicas confirmadas para este ano exato em JSON: {{"dicas_aprovadas": []}}"""
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt_auditoria}],
            temperature=0.0,
            response_format={"type": "json_object"}
        )
        raw_list = json.loads(completion.choices[0].message.content).get("dicas_aprovadas", [])
        return [sanitizar_item(x) for x in raw_list]
    except: return []

def obter_dados_carta():
    tentativas = 0
    while tentativas < 3:
        tema_sorteado = random.choice(["PESSOA", "LUGAR", "ANO", "DIGITAL", "COISA"])
        proibidos_str = ", ".join([str(x) for x in st.session_state.used_answers[-20:]])
        
        prompt_especifico = "- RESPOSTA: ANO 4 DÍGITOS." if tema_sorteado == "ANO" else "- RESPOSTA: Algo famoso mundialmente."
        
        prompt = f"""Jogo Perfil. Tema: {tema_sorteado}. {prompt_especifico} Proibido: {proibidos_str}. JSON: {{"tema": "{tema_sorteado}", "dicas": [], "resposta": ""}}"""

        try:
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5,
                response_format={"type": "json_object"}
            )
            dados = json.loads(completion.choices[0].message.content)
            
            # Sanitiza Resposta
            resposta_atual = sanitizar_item(dados.get("resposta", "Desconhecido"))
            
            # Sanitiza Lista Inicial de Dicas
            dicas_raw = dados.get("dicas", [])
            if not isinstance(dicas_raw, list): dicas_raw = []
            dicas_limpas = [sanitizar_item(d) for d in dicas_raw]

            if verificar_similaridade(resposta_atual): 
                tentativas += 1; continue
            
            if tema_sorteado == "ANO":
                dicas_limpas = auditar_dicas_ano(resposta_atual, dicas_limpas)

            # Filtro de Spoilers (Agora seguro porque tudo é string)
            palavras_proibidas = [p for p in resposta_atual.lower().split() if len(p) > 3]
            dicas_sem_spoiler = [d for d in dicas_limpas if not any(p in d.lower() for p in palavras_proibidas)]

            # Preenchimento Inteligente
            ciclos = 0
            while len(dicas_sem_spoiler) < 20 and ciclos < 2:
                novas = gerar_dicas_complementares(resposta_atual, 22-len(dicas_sem_spoiler), tema_sorteado)
                # 'novas' já vem sanitizada da função
                dicas_sem_spoiler += [nd for nd in novas if not any(p in nd.lower() for p in palavras_proibidas)]
                ciclos += 1

            if len(dicas_sem_spoiler) < 18: 
                tentativas += 1; continue

            # Montagem Final da Carta
            dicas_finais = []
            dica_idx = 0
            
            # Vamos iterar 20 vezes para criar as posições
            for i in range(20):
                if i == 1: # Posição 2 (índice 1)
                    dicas_finais.append("2. PERCA A VEZ")
                elif i == 11: # Posição 12 (índice 11)
                    dicas_finais.append("12. UM PALPITE A QUALQUER HORA")
                else:
                    if dica_idx < len(dicas_sem_spoiler):
                        dicas_finais.append(dicas_sem_spoiler[dica_idx])
                        dica_idx += 1
                    else:
                        break # Acabaram as dicas reais

            dados['dicas'] = dicas_finais
            dados['resposta'] = resposta_atual # Garante que vai a versão limpa
            st.session_state.used_answers.append(resposta_atual)
            return dados
            
        except Exception as e: 
            registrar_log(f"Erro: {e}")
            tentativas += 1
    return None

# --- INTERFACE ---

if not st.session_state.carta:
    st.markdown("""
        <div style="text-align: center; padding: 20px 0;">
            <img src="https://img.icons8.com/3d-fluency/94/dice.png" class="golden-dice-icon">
            <h1 class="main-title">Perfil 7</h1>
            <p class="subtitle">Adivinhe quem ou o que eu sou!</p>
        </div>
    """, unsafe_allow_html=True)
    
    if st.button("✨ GERAR NOVA CARTA", use_container_width=True):
        if st.session_state.reserva:
            st.session_state.carta = st.session_state.reserva
            st.session_state.reserva = None
            st.rerun()
        else:
            with st.spinner('Auditando fatos...'):
                st.session_state.carta = obter_dados_carta()
                if st.session_state.carta:
                    st.rerun()

else:
    c = st.session_state.carta
    st.markdown(f"""
    <div class="card-theme-box">
        <div style="font-size: 11px; color: #95a5a6; font-weight: 700;">DIGA AOS JOGADORES QUE SOU UM(A):</div>
        <div class="theme-value">{c.get('tema')}</div>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("👁️ REVELAR RESPOSTA", use_container_width=True): 
        st.session_state.revelado = True

    if st.session_state.revelado:
        st.success(f"🏆 RESPOSTA: {c.get('resposta')}")

    tips_html = '<div class="card-tips-box">'
    for idx, dica in enumerate(c.get('dicas', [])):
        # Força string para evitar erro na interface também
        dica_str = str(dica)
        display_text = dica_str if (len(dica_str) > 0 and dica_str[0].isdigit()) else f"{idx+1}. {dica_str}"
        
        if "PERCA A VEZ" in display_text.upper():
            tips_html += f"<div class='hint-row' style='color:#d63031; background: #ffe6e6; border-radius: 5px; padding: 10px;'>🚫 {display_text}</div>"
        elif "PALPITE" in display_text.upper():
            tips_html += f"<div class='hint-row' style='color:#27ae60; background: #e6ffea; border-radius: 5px; padding: 10px;'>💡 {display_text}</div>"
        else:
            tips_html += f"<div class='hint-row'>{display_text}</div>"
    tips_html += '</div>'
    st.markdown(tips_html, unsafe_allow_html=True)
    
    st.write("") 
    
    if st.button("🔄 PRÓXIMA CARTA", use_container_width=True):
        st.session_state.carta = None
        st.session_state.revelado = False
        st.rerun()

    if st.session_state.reserva is None:
        st.session_state.reserva = obter_dados_carta()

st.divider()
with st.expander("🛠️ Debug Logs"):
    for log in st.session_state.logs[-5:]:
        st.markdown(f"<div class='log-text'>{log}</div>", unsafe_allow_html=True)
