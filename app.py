import streamlit as st
from groq import Groq
import json
import random
import difflib
import time
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Perfil 7 AI", page_icon="🎲", layout="centered", initial_sidebar_state="collapsed")

# --- CONEXÃO COM GOOGLE SHEETS (BANCO DE DADOS) ---
def conectar_banco():
    """Conecta na planilha e retorna a lista de palavras já usadas"""
    try:
        # Tenta pegar as credenciais dos secrets
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        
        # Cria um dicionário com as credenciais do TOML
        creds_dict = dict(st.secrets["gcp_service_account"])
        
        # Corrige a quebra de linha da chave privada se necessário
        if "private_key" in creds_dict:
            creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")

        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        
        # Abre a planilha pelo nome (tem que ser exato)
        sheet = client.open("banco_perfil").sheet1 
        
        # Pega todos os valores da primeira coluna
        palavras = sheet.col_values(1)
        
        # Remove o cabeçalho se existir
        if palavras and palavras[0] == "PALAVRAS_USADAS":
            palavras.pop(0)
            
        return sheet, palavras
    except Exception as e:
        st.error(f"Erro ao conectar no banco de dados: {e}")
        return None, []

def salvar_no_banco(sheet, palavra):
    """Salva a nova palavra na planilha"""
    try:
        if sheet:
            sheet.append_row([palavra])
    except Exception as e:
        print(f"Erro ao salvar: {e}")

# --- INICIALIZAÇÃO DO BANCO ---
if 'sheet_con' not in st.session_state:
    sheet, usadas_db = conectar_banco()
    st.session_state.sheet_con = sheet
    # Mescla o que já está na sessão com o que veio do banco
    if 'used_answers' not in st.session_state:
        st.session_state.used_answers = []
    
    # Adiciona as do banco à lista de bloqueio
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

# --- CSS RESPONSIVO (MANTIDO) ---
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
    @keyframes floater { 0% { transform: translateY(0px); } 50% { transform: translateY(-10px); } 100% { transform: translateY(0px); } }
    </style>
    """, unsafe_allow_html=True)

# --- FUNÇÕES AUXILIARES ---
def sanitizar_item(item):
    if isinstance(item, str): return item.strip()
    elif isinstance(item, dict): return str(list(item.values())[0]).strip()
    return str(item)

def verificar_similaridade(nova_resposta):
    nova = sanitizar_item(nova_resposta).lower()
    # Verifica em toda a base histórica
    for usada in st.session_state.used_answers:
        usada_clean = sanitizar_item(usada).lower()
        if nova == usada_clean: return True # Exata
        if nova in usada_clean or usada_clean in nova: return True # Contida
        if difflib.SequenceMatcher(None, nova, usada_clean).ratio() > 0.85: return True # Similar
    return False

def gerar_dicas_complementares(resposta, qtd, tema):
    prompt = f"Jogo sobre: {resposta} (Tema: {tema}). Gere {qtd} fatos CURTOS e CURIOSOS. Resposta '{resposta}' PROIBIDA no texto. JSON: {{'dicas': []}}"
    try:
        resp = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role":"user","content":prompt}], response_format={"type":"json_object"})
        return [sanitizar_item(x) for x in json.loads(resp.choices[0].message.content).get('dicas', [])]
    except: return []

def obter_dados_carta():
    tentativas = 0
    while tentativas < 4:
        tema = random.choice(["PESSOA", "LUGAR", "ANO", "DIGITAL", "COISA"])
        # Pega uma amostra aleatória das proibidas para não estourar o prompt
        amostra_proibida = random.sample(st.session_state.used_answers, min(len(st.session_state.used_answers), 50))
        proibidos_str = ", ".join(amostra_proibida)
        
        prompt = f"Jogo Perfil. Tema: {tema}. Resposta deve ser DIFÍCIL e FAMOSA. PROIBIDO: {proibidos_str}. JSON: {{'tema': '{tema}', 'dicas': [], 'resposta': ''}}"
        
        try:
            resp = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role":"user","content":prompt}], temperature=0.6, response_format={"type":"json_object"})
            dados = json.loads(resp.choices[0].message.content)
            resposta = sanitizar_item(dados.get('resposta', ''))
            
            if verificar_similaridade(resposta):
                tentativas += 1; continue
                
            dicas = [sanitizar_item(d) for d in dados.get('dicas', [])]
            # Remove spoilers
            dicas = [d for d in dicas if resposta.lower() not in d.lower()]
            
            # Completa dicas se faltar
            while len(dicas) < 20:
                novas = gerar_dicas_complementares(resposta, 22-len(dicas), tema)
                dicas.extend([n for n in novas if resposta.lower() not in n.lower()])
                if not novas: break
            
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
            
            # --- SALVAMENTO NO BANCO ---
            st.session_state.used_answers.append(resposta) # Atualiza memória local
            salvar_no_banco(st.session_state.sheet_con, resposta) # Salva no Google Sheets
            
            return dados
        except Exception as e:
            tentativas += 1
    return None

# --- INTERFACE ---
if 'carta' not in st.session_state: st.session_state.carta = None
if 'revelado' not in st.session_state: st.session_state.revelado = False

if not st.session_state.carta:
    st.markdown("""<div style="text-align: center; padding: 20px 0;"><img src="https://img.icons8.com/3d-fluency/94/dice.png" class="golden-dice-icon"><h1 class="main-title">Perfil 7</h1><p class="subtitle">Nunca repete uma resposta!</p></div>""", unsafe_allow_html=True)
    if st.button("✨ GERAR CARTA", use_container_width=True):
        with st.spinner('Consultando banco de dados e gerando...'):
            st.session_state.carta = obter_dados_carta()
            st.rerun()
else:
    c = st.session_state.carta
    st.markdown(f"""<div class="card-theme-box"><div style="font-size: 11px; color: #95a5a6; font-weight: 700;">SOU UM(A):</div><div class="theme-value">{c.get('tema')}</div></div>""", unsafe_allow_html=True)
    
    if st.button("👁️ REVELAR", use_container_width=True): st.session_state.revelado = True
    if st.session_state.revelado: st.success(f"🏆 {c.get('resposta')}")

    html = '<div class="card-tips-box">'
    for i, d in enumerate(c.get('dicas', [])):
        txt = d if d[0].isdigit() else f"{i+1}. {d}"
        style = "color:#d63031; bg:#ffe6e6;" if "PERCA" in txt else ("color:#27ae60; bg:#e6ffea;" if "PALPITE" in txt else "")
        html += f"<div class='hint-row' style='{style}'>{txt}</div>"
    st.markdown(html + "</div>", unsafe_allow_html=True)
    
    if st.button("🔄 PRÓXIMA", use_container_width=True):
        st.session_state.carta = None
        st.session_state.revelado = False
        st.rerun()
