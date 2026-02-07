import streamlit as st
from groq import Groq
import json
import random
import difflib
import time
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Perfil 7 AI",
    page_icon="🎲",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- SISTEMA DE LOGS ---
if 'logs' not in st.session_state: st.session_state.logs = []

def registrar_log(msg):
    timestamp = time.strftime("%H:%M:%S")
    formatted_msg = f"[{timestamp}] {msg}"
    st.session_state.logs.append(formatted_msg)
    # Mantém apenas os últimos 50 logs para não pesar
    if len(st.session_state.logs) > 50:
        st.session_state.logs.pop(0)

# --- CONEXÃO COM GOOGLE SHEETS (BANCO DE DADOS) ---
def conectar_banco():
    """Conecta na planilha e retorna a lista de palavras já usadas"""
    registrar_log("🔌 Conectando ao Banco de Dados (Google Sheets)...")
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        
        # Carrega credenciais
        if "gcp_service_account" not in st.secrets:
            registrar_log("❌ Erro: Secrets do Google não encontrados.")
            return None, []
            
        creds_dict = dict(st.secrets["gcp_service_account"])
        
        # Corrige quebras de linha na chave privada
        if "private_key" in creds_dict:
            creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")

        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        
        # Abre a planilha
        sheet = client.open("banco_perfil").sheet1 
        
        # Pega valores
        palavras = sheet.col_values(1)
        
        # Remove cabeçalho
        if palavras and palavras[0] == "PALAVRAS_USADAS":
            palavras.pop(0)
            
        registrar_log(f"✅ Banco conectado! {len(palavras)} palavras carregadas.")
        return sheet, palavras
    except Exception as e:
        registrar_log(f"❌ Falha na conexão com Banco: {e}")
        return None, []

def salvar_no_banco(sheet, palavra):
    """Salva a nova palavra na planilha"""
    try:
        if sheet:
            sheet.append_row([palavra])
            registrar_log(f"💾 Palavra '{palavra}' salva no banco de dados.")
    except Exception as e:
        registrar_log(f"⚠️ Erro ao salvar no banco: {e}")

# --- INICIALIZAÇÃO DO BANCO NA SESSÃO ---
if 'sheet_con' not in st.session_state:
    sheet, usadas_db = conectar_banco()
    st.session_state.sheet_con = sheet
    
    if 'used_answers' not in st.session_state:
        st.session_state.used_answers = []
    
    # Adiciona as do banco à memória local
    st.session_state.used_answers.extend(usadas_db)
    # Remove duplicatas
    st.session_state.used_answers = list(set(st.session_state.used_answers))

# --- CONFIGURAÇÃO DA GROQ ---
try:
    if "GROQ_API_KEY" in st.secrets:
        api_key = st.secrets["GROQ_API_KEY"]
    else:
        api_key = "teste"
    client = Groq(api_key=api_key)
except Exception:
    st.error("ERRO: Configure GROQ_API_KEY.")
    st.stop()

# --- CSS RESPONSIVO ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;800&display=swap');
    .stApp { background: linear-gradient(135deg, rgba(40,15,65,1) 0%, rgba(86,22,86,1) 30%, rgba(186,75,35,1) 65%, rgba(232,183,77,1) 100%); background-attachment: fixed; font-family: 'Montserrat', sans-serif; }
    .main-title { font-size: clamp(45px, 12vw, 90px) !important; font-weight: 800; color: #F3C623; text-align: center; text-shadow: 0 0 15px rgba(243, 198, 35, 0.6); margin: 0; line-height: 1.1; }
    .subtitle { font-size: clamp(18px, 5vw, 26px); color: white; text-align: center; margin-bottom: 20px; }
    .card-theme-box { background: white; padding: 15px; border-radius: 15px; border: 4px solid #FFD700; text-align: center; margin-bottom: 15px; }
    .theme-value { font-size: clamp(24px, 7vw, 32px); font-weight: 900; color: #2c3e50; text-transform: uppercase; }
    .card-tips-box { background: white; padding: 5px 15px; border-radius: 15px; border: 4px solid #FFD700; margin-top: 15px; }
    .hint-row { border-bottom: 1px solid #e0e0e0; padding: 10px 0; font-weight: 700; color: #1e272e; font-size: clamp(14px, 4vw, 16px); }
    .stButton > button { background: linear-gradient(90deg, #ff9f43, #feca57, #ff9f43); color: #5d2e01; font-weight: 800; border-radius: 50px !important; border: 3px solid #fff200; }
    .golden-dice-icon { width: clamp(80px, 20vw, 130px); display: block; margin: 20px auto 10px auto; animation: floater 3s ease-in-out infinite; }
    .log-text { font-family: monospace; font-size: 11px; color: #00ff00; background: black; padding: 5px; margin-bottom: 2px; }
    @keyframes floater { 0% { transform: translateY(0px); } 50% { transform: translateY(-10px); } 100% { transform: translateY(0px); } }
    </style>
    """, unsafe_allow_html=True)

# --- FUNÇÕES AUXILIARES ---
def sanitizar_item(item):
    """Limpa e garante que o item seja string"""
    if isinstance(item, str): return item.strip()
    elif isinstance(item, dict): return str(list(item.values())[0]).strip()
    return str(item)

def verificar_similaridade(nova_resposta):
    """Verifica se a resposta já saiu (Local + Banco)"""
    nova = sanitizar_item(nova_resposta).lower()
    for usada in st.session_state.used_answers:
        usada_clean = sanitizar_item(usada).lower()
        # Verificação exata
        if nova == usada_clean: return True 
        # Verificação de substring
        if nova in usada_clean or usada_clean in nova: return True 
        # Verificação aproximada (fuzzy)
        if difflib.SequenceMatcher(None, nova, usada_clean).ratio() > 0.85: return True 
    return False

def gerar_dicas_complementares(resposta, qtd, tema):
    registrar_log(f"➕ Gerando +{qtd} dicas extras...")
    prompt = f"Jogo sobre: {resposta} (Tema: {tema}). Gere {qtd} fatos CURTOS e CURIOSOS. Resposta '{resposta}' PROIBIDA no texto. JSON: {{'dicas': []}}"
    try:
        resp = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role":"user","content":prompt}], response_format={"type":"json_object"})
        raw_list = json.loads(resp.choices[0].message.content).get('dicas', [])
        return [sanitizar_item(x) for x in raw_list]
    except: return []

def obter_dados_carta():
    tentativas = 0
    registrar_log("🎲 Iniciando geração de carta...")
    
    while tentativas < 4:
        tema = random.choice(["PESSOA", "LUGAR", "ANO", "DIGITAL", "COISA"])
        registrar_log(f"Tentativa {tentativas+1}: Tema '{tema}'")
        
        # Amostragem para não estourar o prompt (pega 50 aleatórias das já usadas)
        total_usadas = len(st.session_state.used_answers)
        amostra_proibida = random.sample(st.session_state.used_answers, min(total_usadas, 50))
        proibidos_str = ", ".join(amostra_proibida)
        
        prompt = f"Jogo Perfil. Tema: {tema}. Resposta deve ser DIFÍCIL e FAMOSA. PROIBIDO: {proibidos_str}. JSON: {{'tema': '{tema}', 'dicas': [], 'resposta': ''}}"
        
        try:
            resp = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role":"user","content":prompt}], temperature=0.6, response_format={"type":"json_object"})
            dados = json.loads(resp.choices[0].message.content)
            resposta = sanitizar_item(dados.get('resposta', ''))
            
            registrar_log(f"IA Sugeriu: {resposta}")

            if verificar_similaridade(resposta):
                registrar_log(f"🚫 Repetida ({resposta}). Tentando outra...")
                tentativas += 1; continue
                
            dicas = [sanitizar_item(d) for d in dados.get('dicas', [])]
            # Remove spoilers
            dicas = [d for d in dicas if resposta.lower() not in d.lower()]
            
            # Completa dicas se faltar
            ciclos = 0
            while len(dicas) < 20 and ciclos < 2:
                novas = gerar_dicas_complementares(resposta, 22-len(dicas), tema)
                dicas.extend([n for n in novas if resposta.lower() not in n.lower()])
                ciclos += 1
                if not novas: break
            
            if len(dicas) < 15:
                registrar_log("⚠️ Poucas dicas válidas. Descartando.")
                tentativas += 1; continue

            # Monta lista final
            dicas_finais = []
            idx_dica = 0
            for i in range(20):
                if i == 1: dicas_finais.append("2. PERCA A VEZ")
                elif i == 11: dicas_finais.append("12. UM PALPITE A QUALQUER HORA")
                elif idx_dica < len(dicas):
                    dicas_finais.append(dicas[idx_dica])
                    idx_dica += 1
            
            dados['dicas'] = dicas_finais[:20]
            dados['resposta'] = resposta
            
            # --- SALVAMENTO ---
            st.session_state.used_answers.append(resposta) 
            salvar_no_banco(st.session_state.sheet_con, resposta)
            
            registrar_log("✨ Carta pronta e salva!")
            return dados
        except Exception as e:
            registrar_log(f"💥 Erro no loop: {e}")
            tentativas += 1
    
    registrar_log("❌ Falha após 4 tentativas.")
    return None

# --- INTERFACE ---
if 'carta' not in st.session_state: st.session_state.carta = None
if 'revelado' not in st.session_state: st.session_state.revelado = False

if not st.session_state.carta:
    st.markdown("""<div style="text-align: center; padding: 20px 0;"><img src="https://img.icons8.com/3d-fluency/94/dice.png" class="golden-dice-icon"><h1 class="main-title">Perfil 7</h1><p class="subtitle">Nunca repete uma resposta!</p></div>""", unsafe_allow_html=True)
    if st.button("✨ GERAR CARTA", use_container_width=True):
        registrar_log("🖱️ Botão Clicado: Gerar")
        with st.spinner('Consultando banco de dados e gerando...'):
            st.session_state.carta = obter_dados_carta()
            st.rerun()
else:
    c = st.session_state.carta
    st.markdown(f"""<div class="card-theme-box"><div style="font-size: 11px; color: #95a5a6; font-weight: 700;">SOU UM(A):</div><div class="theme-value">{c.get('tema')}</div></div>""", unsafe_allow_html=True)
    
    if st.button("👁️ REVELAR", use_container_width=True): 
        st.session_state.revelado = True
        registrar_log("👁️ Resposta revelada")

    if st.session_state.revelado: st.success(f"🏆 {c.get('resposta')}")

    html = '<div class="card-tips-box">'
    for i, d in enumerate(c.get('dicas', [])):
        txt = d if d[0].isdigit() else f"{i+1}. {d}"
        style = "color:#d63031; background: #ffe6e6; border-radius: 5px; padding: 10px;" if "PERCA" in txt.upper() else ("color:#27ae60; background: #e6ffea; border-radius: 5px; padding: 10px;" if "PALPITE" in txt.upper() else "")
        html += f"<div class='hint-row' style='{style}'>{txt}</div>"
    st.markdown(html + "</div>", unsafe_allow_html=True)
    
    if st.button("🔄 PRÓXIMA", use_container_width=True):
        registrar_log("🔄 Reiniciando rodada...")
        st.session_state.carta = None
        st.session_state.revelado = False
        st.rerun()

st.divider()
# Área de Logs Restaurada
with st.expander("🛠️ Logs do Sistema (Debug)"):
    if not st.session_state.logs:
        st.write("Aguardando operações...")
    # Mostra do mais recente para o mais antigo
    for log in reversed(st.session_state.logs):
        st.markdown(f"<div class='log-text'>{log}</div>", unsafe_allow_html=True)
