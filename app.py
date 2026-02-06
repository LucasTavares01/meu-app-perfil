import streamlit as st
from groq import Groq
import json
import re
import traceback
import time
import random
import difflib

# --- CONFIGURAÇÃO DE SEGURANÇA (GROQ) ---
try:
    if "GROQ_API_KEY" in st.secrets:
        api_key = st.secrets["GROQ_API_KEY"]
    else:
        api_key = "COLOQUE_SUA_KEY_AQUI_SE_ESTIVER_RODANDO_LOCAL" 
    
    client = Groq(api_key=api_key)
except Exception:
    st.error("ERRO: Configure sua chave 'GROQ_API_KEY' no painel 'Secrets' do Streamlit.")
    st.stop()

# --- CSS (MANTIDO IDÊNTICO) ---
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
    .main .block-container { padding-top: 2rem; }

    div[data-testid="stSpinner"] {
        justify-content: center;
        color: #F3C623;
        font-weight: bold;
        margin-top: 10px;
        margin-bottom: 10px;
    }

    .welcome-box {
        text-align: center;
        padding: 10px;
        margin-bottom: 30px;
    }
    .golden-dice-icon {
        width: 140px;
        display: block;
        margin: 50px auto -20px auto;
        filter: drop-shadow(0 0 30px rgba(243, 198, 35, 0.7));
        animation: floater 3s ease-in-out infinite;
    }
    @keyframes floater {
        0% { transform: translateY(0px); }
        50% { transform: translateY(-12px); }
        100% { transform: translateY(0px); }
    }
    
    .main-title {
        font-size: 100px !important; 
        font-weight: 800;
        color: #F3C623;
        margin: 0;
        text-shadow: 0 0 5px #F3C623, 0 0 20px rgba(243, 198, 35, 0.8), 0 0 40px rgba(243, 198, 35, 0.6), 0 0 60px rgba(243, 198, 35, 0.4);
        text-align: center;
        line-height: 1.1;
        letter-spacing: 1px;
    }
    
    .subtitle {
        font-size: 28px;
        font-weight: 400;
        color: #ffffff;
        margin-top: 10px;
        margin-bottom: 30px;
        text-shadow: 0 2px 5px rgba(0,0,0,0.5);
        text-align: center;
    }
    
    .description {
        font-size: 16px;
        color: #e0e0e0;
        max-width: 400px;
        margin: 0 auto;
        line-height: 1.5;
    }

    .stButton > button {
        background: linear-gradient(90deg, #ff9f43, #feca57, #ff9f43);
        background-size: 200% auto;
        color: #5d2e01;
        font-weight: 800;
        font-size: 18px;
        height: 55px;
        border-radius: 50px !important;
        border: 3px solid #fff200;
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        transition: 0.3s;
        text-transform: uppercase;
    }
    .stButton > button:hover {
        background-position: right center;
        transform: translateY(-2px);
        box-shadow: 0 10px 25px rgba(255, 200, 0, 0.4);
        color: #000;
    }
    .stButton > button:active {
        color: #5d2e01;
        border-color: #fff200;
        background-color: #feca57;
    }

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

    .hint-row { border-bottom: 1px solid #e0e0e0; padding: 12px 5px; font-family: 'Montserrat', sans-serif; font-size: 16px; font-weight: 700; color: #1e272e; line-height: 1.4; }
    .special-loss { background-color: #ff7675; color: white !important; padding: 12px; border-radius: 8px; border: none; text-align: center; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
    .special-guess { background-color: #2ed573; color: white !important; padding: 12px; border-radius: 8px; border: none; text-align: center; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
    .stSuccess { text-align: center; font-weight: bold; font-size: 18px; border-radius: 15px; }
    
    .log-text { font-family: monospace; font-size: 12px; color: #00ff00; background: black; padding: 5px; margin-bottom: 2px; }
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

def verificar_similaridade(nova_resposta):
    """Verifica se a resposta já saiu"""
    nova = nova_resposta.lower().strip()
    for usada in st.session_state.used_answers:
        usada_clean = usada.lower().strip()
        if nova in usada_clean or usada_clean in nova:
            return True
        similaridade = difflib.SequenceMatcher(None, nova, usada_clean).ratio()
        if similaridade > 0.8:
            return True
    return False

def selecionar_dicas_sem_spoiler(todas_dicas, resposta):
    """
    Filtra as dicas que contém a resposta. 
    Descarta a dica inteira e usa as dicas EXTRAS que pedimos para a IA.
    """
    # Palavras proibidas (Ex: "Praça da Sé" -> ["praça", "sé"])
    # Ignora palavras curtas ("da", "de", "o")
    palavras_proibidas = [p for p in resposta.lower().split() if len(p) > 3]
    
    dicas_aprovadas = []
    
    for dica in todas_dicas:
        if len(dicas_aprovadas) >= 20: # Já temos as 20 necessárias
            break
            
        dica_lower = dica.lower()
        
        # Se for item especial, passa direto
        if "PERCA A VEZ" in dica.upper() or "PALPITE" in dica.upper():
            dicas_aprovadas.append(dica)
            continue
            
        # Verifica se tem spoiler
        tem_spoiler = False
        for palavra in palavras_proibidas:
            if palavra in dica_lower:
                tem_spoiler = True
                # Loga que descartou para debug
                registrar_log(f"Dica descartada (Spoiler '{palavra}'): {dica[:30]}...")
                break
        
        # Se NÃO tem spoiler, aprova
        if not tem_spoiler:
            dicas_aprovadas.append(dica)
            
    # Se por azar faltar dica (muito spoiler), completa com genérica
    while len(dicas_aprovadas) < 20:
        dicas_aprovadas.append(f"{len(dicas_aprovadas)+1}. Fato adicional sobre este tema.")
        
    return dicas_aprovadas

# --- LÓGICA DE GERAÇÃO ---
def obter_dados_carta():
    tentativas = 0
    max_tentativas = 3 
    
    while tentativas < max_tentativas:
        # 1. ROLETA DE TEMAS
        temas_possiveis = ["PESSOA", "LUGAR", "ANO", "DIGITAL", "COISA"]
        tema_sorteado = random.choice(temas_possiveis)
        
        proibidos_str = ", ".join(st.session_state.used_answers[-20:]) 
        
        registrar_log(f"Tentativa {tentativas+1}: Sorteado '{tema_sorteado}'.")
        
        # PROMPT: PEDIMOS 25 DICAS PARA TER "GORDURA" PARA QUEIMAR
        prompt = f"""
        Você é o criador oficial do jogo 'Perfil'.
        
        TAREFA: Criar uma carta para o tema OBRIGATÓRIO: "{tema_sorteado}".
        
        REGRAS CRÍTICAS:
        1. Se o tema for 'ANO': A resposta deve ser APENAS O NÚMERO (Ex: 1988). Sem 'A.C.' ou texto.
        2. GERE 25 DICAS (para que eu possa descartar as que tiverem spoiler).
        3. A resposta NÃO PODE aparecer no texto das dicas.
        
        PROIBIDO REPETIR: {proibidos_str}
        
        ESTILO PERFIL (DIFÍCIL E CURIOSO):
        - Use fatos obscuros, números exatos, materiais e história.
        - Nada de "É famoso" ou "Fica na Ásia".
        
        ESTRUTURA DA LISTA DE DICAS:
        - 30% chance de ter 1 'PERCA A VEZ'.
        - 30% chance de ter 1 'UM PALPITE A QUALQUER HORA'.
        
        Retorne APENAS JSON.
        FORMATO: {{"tema": "{tema_sorteado}", "dicas": ["1. ...", ... "25. ..."], "resposta": "NOME"}}
        """
        
        try:
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "Você é uma API JSON. Responda apenas JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.85, 
                max_tokens=1800, # Aumentei token pois pedimos 25 dicas
                top_p=1,
                stream=False,
                response_format={"type": "json_object"}
            )
            
            content = completion.choices[0].message.content
            dados = json.loads(content)
            
            # Validações Básicas
            dados["tema"] = tema_sorteado
            resposta_atual = dados["resposta"]
            
            # Anti-Repetição
            if verificar_similaridade(resposta_atual):
                registrar_log(f"REPETIDA: '{resposta_atual}'. Retentando...")
                tentativas += 1
                continue 
            
            # Limpeza de Ano
            if tema_sorteado == "ANO":
                apenas_numeros = re.sub("[^0-9]", "", str(resposta_atual))
                if len(apenas_numeros) == 4:
                    dados["resposta"] = apenas_numeros
            
            st.session_state.used_answers.append(resposta_atual)
            
            # --- FILTRAGEM DE SPOILERS (A GRANDE MUDANÇA) ---
            # Pegamos as 25 dicas brutas e selecionamos as 20 melhores sem a resposta
            dicas_brutas = dados.get('dicas', [])
            dicas_filtradas = selecionar_dicas_sem_spoiler(dicas_brutas, resposta_atual)
            
            # --- FORMATAÇÃO FINAL (Itens Especiais) ---
            dicas_finais = []
            tem_perca = False
            tem_palpite = False
            
            for dica in dicas_filtradas:
                d_upper = dica.upper()
                
                if "PERCA A VEZ" in d_upper:
                    if not tem_perca:
                        dicas_finais.append("2. PERCA A VEZ") # Posição 2 estética, mas embaralhada depois
                        tem_perca = True
                    else:
                        dicas_finais.append(f"{len(dicas_finais)+1}. Curiosidade extra sobre o tema.")
                        
                elif "PALPITE" in d_upper:
                    if not tem_palpite:
                        dicas_finais.append("6. UM PALPITE A QUALQUER HORA")
                        tem_palpite = True
                    else:
                        dicas_finais.append(f"{len(dicas_finais)+1}. Fato histórico sobre o tema.")
                else:
                    dicas_finais.append(dica)
            
            dados['dicas'] = dicas_finais[:20] # Corta em 20 exatas
            
            registrar_log(f"Carta Aprovada: {resposta_atual} ({tema_sorteado})")
            return dados
            
        except Exception as e:
            registrar_log(f"Erro na geração: {e}")
            tentativas += 1
            
    registrar_log("Falha após 3 tentativas.")
    return None

# --- INTERFACE ---

if not st.session_state.carta:
    # --- TELA INICIAL ---
    st.markdown("""
        <div class="welcome-box">
            <img src="https://img.icons8.com/3d-fluency/94/dice.png" class="golden-dice-icon">
            <h1 class="main-title">Perfil 7</h1>
            <div class="subtitle">Bem-vindo!</div>
            <div class="description">Clique abaixo para gerar uma nova carta com Inteligência Artificial.</div>
        </div>
    """, unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns([1, 2, 1]) 
    with c2:
        if st.button("✨ GERAR NOVA CARTA", use_container_width=True):
            registrar_log("Iniciando...")
            
            if st.session_state.reserva:
                st.session_state.carta = st.session_state.reserva
                st.session_state.reserva = None 
                st.session_state.revelado = False
                st.rerun()
            else:
                with st.spinner('Sorteando tema e pesquisando fatos...'):
                    st.session_state.carta = obter_dados_carta()
                    if st.session_state.carta:
                        st.session_state.reserva = obter_dados_carta()
                        st.rerun()
                    else:
                        st.error("Erro ao conectar. Tente novamente.")

else:
    c = st.session_state.carta
    
    st.markdown(f"""
    <div class="card-theme-box">
        <div class="header-label">DIGA AOS JOGADORES QUE SOU UM(A):</div>
        <div class="theme-value">{c.get('tema', 'TEMA')}</div>
    </div>
    """, unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        if st.button("👁️ REVELAR RESPOSTA", use_container_width=True): 
            st.session_state.revelado = True

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
    
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        if st.button("🔄 NOVA CARTA", use_container_width=True):
            registrar_log("Voltando...")
            st.session_state.carta = None
            st.rerun()

    # Recarga em background
    if st.session_state.carta and st.session_state.reserva is None:
        registrar_log("Criando próxima (com tema aleatório)...")
        nova_reserva = obter_dados_carta()
        if nova_reserva:
            st.session_state.reserva = nova_reserva
            registrar_log("Próxima pronta!")

# --- PAINEL DE LOGS ---
st.divider()
with st.expander("🛠️ Logs do Sistema (Debug)"):
    if not st.session_state.logs:
        st.write("Nenhum log registrado.")
    for log_item in st.session_state.logs[-15:]:
        st.markdown(f"<div class='log-text'>{log_item}</div>", unsafe_allow_html=True)
