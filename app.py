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
    palavras_proibidas = [p for p in resposta.lower().split() if len(p) > 3]
    dicas_aprovadas = []
    
    for dica in todas_dicas:
        if len(dicas_aprovadas) >= 20: 
            break
            
        dica_lower = dica.lower()
        if "PERCA A VEZ" in dica.upper() or "PALPITE" in dica.upper():
            dicas_aprovadas.append(dica)
            continue
            
        tem_spoiler = False
        for palavra in palavras_proibidas:
            if palavra in dica_lower:
                tem_spoiler = True
                registrar_log(f"Spoiler removido: {dica[:30]}...")
                break
        
        if not tem_spoiler:
            dicas_aprovadas.append(dica)
            
    while len(dicas_aprovadas) < 20:
        dicas_aprovadas.append(f"{len(dicas_aprovadas)+1}. Fato adicional verificado sobre este tema.")
        
    return dicas_aprovadas

# --- NOVA FUNÇÃO: O AUDITOR DE ANOS ---
def auditar_dicas_ano(ano_alvo, lista_dicas_candidatas):
    """
    Esta função chama a IA novamente para agir como um auditor chato.
    Ela deve filtrar impiedosamente qualquer dica que não seja do ano exato.
    """
    registrar_log(f"🔍 Iniciando auditoria rigorosa para o ano {ano_alvo}...")
    
    prompt_auditoria = f"""
    Você é um Auditor Histórico Rigoroso.
    O ano alvo é: {ano_alvo}.
    
    Abaixo está uma lista de fatos candidatos.
    Sua missão:
    1. Verificar se o fato ocorreu EXATAMENTE em {ano_alvo}.
    2. Se ocorreu em {int(ano_alvo)-1} ou {int(ano_alvo)+1}, REJEITE.
    3. Se for uma década, REJEITE.
    4. Se for um fato genérico (matemática, ciência) que não depende do ano, REJEITE.
    
    Retorne APENAS um JSON com a lista 'dicas_aprovadas' contendo as strings originais que são 100% verdadeiras.
    
    LISTA PARA AUDITAR:
    {json.dumps(lista_dicas_candidatas)}
    """
    
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "Você é um verificador de fatos. Você elimina mentiras e imprecisões."},
                {"role": "user", "content": prompt_auditoria}
            ],
            temperature=0.0, # Zero criatividade, apenas lógica
            max_tokens=2000,
            response_format={"type": "json_object"}
        )
        
        content = completion.choices[0].message.content
        dados = json.loads(content)
        aprovadas = dados.get("dicas_aprovadas", [])
        
        registrar_log(f"Auditoria concluída. {len(aprovadas)} dicas sobreviveram de {len(lista_dicas_candidatas)}.")
        return aprovadas
        
    except Exception as e:
        registrar_log(f"Erro na auditoria: {e}")
        return [] # Se falhar, retorna vazio para forçar regeneração

# --- LÓGICA DE GERAÇÃO PRINCIPAL ---
def obter_dados_carta():
    tentativas = 0
    max_tentativas = 3 
    
    while tentativas < max_tentativas:
        temas_possiveis = ["PESSOA", "LUGAR", "ANO", "DIGITAL", "COISA"]
        tema_sorteado = random.choice(temas_possiveis)
        
        proibidos_str = ", ".join(st.session_state.used_answers[-20:]) 
        
        registrar_log(f"Tentativa {tentativas+1}: '{tema_sorteado}'.")
        
        # DEFINIÇÃO DOS PROMPTS
        if tema_sorteado == "ANO":
            # Para ANOS: Pedimos 35 dicas para ter gordura para a auditoria cortar
            prompt_especifico = """
            DIRETRIZES OBRIGATÓRIAS PARA 'ANO':
            1. A RESPOSTA deve ser um ANO NUMÉRICO DE 4 DÍGITOS (Ex: 1994, 1822).
            2. GERE 30 DICAS CANDIDATAS. Preciso de muitas opções.
            3. Use: Lançamento de filmes, nascimentos/mortes, tratados, invenções, álbuns musicais.
            4. Tente ser preciso, mas se errar, o auditor cortará depois.
            """
        elif tema_sorteado == "PESSOA":
            prompt_especifico = """
            DIRETRIZES OBRIGATÓRIAS PARA 'PESSOA':
            1. FAMA MUNDIAL OBRIGATÓRIA. (Ex: Einstein, Madonna, Cristiano Ronaldo).
            2. PROIBIDO celebridades locais, apresentadores de TV regionais ou políticos de pouca expressão.
            3. A pessoa deve ser reconhecida em pelo menos 3 continentes.
            4. Use fatos biográficos, prêmios, obras e polêmicas.
            """
        else:
            prompt_especifico = """
            DIRETRIZES PARA LUGAR/DIGITAL/COISA:
            - Evite o óbvio.
            - Se for LUGAR: Turístico global ou capital importante.
            - Se for DIGITAL: Grandes empresas ou tecnologias revolucionárias.
            """

        prompt = f"""
        Você é o criador oficial do jogo 'Perfil'.
        TAREFA: Criar carta para o tema: "{tema_sorteado}".
        {prompt_especifico}
        
        REGRAS GERAIS:
        1. A resposta NÃO PODE aparecer no texto das dicas.
        2. PROIBIDO REPETIR: {proibidos_str}
        
        Retorne APENAS JSON.
        FORMATO: {{"tema": "{tema_sorteado}", "dicas": ["..."], "resposta": "NOME"}}
        """
        
        try:
            # GERAÇÃO INICIAL
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3, 
                max_tokens=2000,
                response_format={"type": "json_object"}
            )
            
            content = completion.choices[0].message.content
            dados = json.loads(content)
            
            dados["tema"] = tema_sorteado
            resposta_atual = dados["resposta"]
            
            # Validações Iniciais
            if verificar_similaridade(resposta_atual):
                tentativas += 1
                continue 
            
            if tema_sorteado == "ANO":
                apenas_numeros = re.sub("[^0-9]", "", str(resposta_atual))
                if len(apenas_numeros) != 4:
                    tentativas += 1
                    continue
                dados["resposta"] = apenas_numeros
                
                # --- FASE DE AUDITORIA (SÓ PARA ANOS) ---
                dicas_auditadas = auditar_dicas_ano(dados["resposta"], dados.get("dicas", []))
                
                # Se sobrar menos de 15 dicas verdadeiras, a carta é descartada e gera outra
                if len(dicas_auditadas) < 15:
                    registrar_log(f"Carta reprovida na auditoria (Só {len(dicas_auditadas)} dicas válidas). Tentando outro ano...")
                    tentativas += 1
                    continue
                
                # Atualiza as dicas com as aprovadas pelo auditor
                dados["dicas"] = dicas_auditadas

            st.session_state.used_answers.append(resposta_atual)
            
            # Formatação Final (Anti-Spoiler + Especiais)
            dicas_brutas = dados.get('dicas', [])
            dicas_filtradas = selecionar_dicas_sem_spoiler(dicas_brutas, resposta_atual)
            
            dicas_finais = []
            tem_perca = False
            tem_palpite = False
            
            for dica in dicas_filtradas:
                d_upper = dica.upper()
                if "PERCA A VEZ" in d_upper:
                    if not tem_perca:
                        dicas_finais.append("2. PERCA A VEZ") 
                        tem_perca = True
                    else:
                        dicas_finais.append(f"{len(dicas_finais)+1}. Curiosidade extra sobre {resposta_atual}.")
                elif "PALPITE" in d_upper:
                    if not tem_palpite:
                        dicas_finais.append("6. UM PALPITE A QUALQUER HORA")
                        tem_palpite = True
                    else:
                        dicas_finais.append(f"{len(dicas_finais)+1}. Detalhe histórico sobre {resposta_atual}.")
                else:
                    dicas_finais.append(dica)
            
            # Se a auditoria cortou muita coisa, completamos com genéricas seguras para não quebrar o layout
            while len(dicas_finais) < 20:
                 dicas_finais.append(f"{len(dicas_finais)+1}. Este fato é amplamente estudado em história.")

            dados['dicas'] = dicas_finais[:20]
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
                with st.spinner('Pesquisando fatos e auditando datas...'):
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
        registrar_log("Criando próxima (Auditoria em andamento)...")
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
