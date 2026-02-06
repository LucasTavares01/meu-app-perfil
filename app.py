import streamlit as st
from groq import Groq
import json
import re
import traceback
import time
import random
import difflib

# ================= CONFIG GROQ =================

if "GROQ_API_KEY" in st.secrets:
    api_key = st.secrets["GROQ_API_KEY"]
else:
    api_key = "COLOQUE_SUA_KEY_AQUI"

client = Groq(api_key=api_key)

# ================= CSS =================

st.markdown("""<style>/* SEU CSS ORIGINAL AQUI */</style>""", unsafe_allow_html=True)

# ================= STATE =================

for k in ["carta","reserva","revelado","logs","used_answers"]:
    if k not in st.session_state:
        st.session_state[k] = [] if k in ["logs","used_answers"] else None

# ================= UTILS =================

def registrar_log(m):
    st.session_state.logs.append(f"[{time.strftime('%H:%M:%S')}] {m}")

def verificar_similaridade(nova):
    for usada in st.session_state.used_answers:
        if difflib.SequenceMatcher(None,nova.lower(),usada.lower()).ratio()>0.8:
            return True
    return False

# ================= AUDITOR DE ANO =================

def auditar_carta_ano(dados):
    prompt=f"""
Ano:{dados['resposta']}
Verifique se TODAS as dicas pertencem a este ano.
Retorne JSON:
{{"valido":true/false,"erros":[]}}
DICAS:{json.dumps(dados['dicas'],ensure_ascii=False)}
"""

    r=client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role":"user","content":prompt}],
        temperature=0,
        max_tokens=500,
        response_format={"type":"json_object"}
    )

    return json.loads(r.choices[0].message.content)

# ================= GERADOR =================

def obter_dados_carta():

    for tentativa in range(5):

        tema=random.choice(["ANO","DIGITAL","PESSOA","LUGAR","COISA"])

        registrar_log(f"Tentativa {tentativa+1}: {tema}")

        prompt=f"""
Você é um auditor factual.

Gere EXATAMENTE 20 dicas.
Todas devem ser 100% verdadeiras.

Tema:{tema}

Se ANO:
- todos eventos devem ser daquele ano.

Formato JSON:
{{"tema":"{tema}","resposta":"X","dicas":["1...","2..."]}}
"""

        try:
            r=client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role":"user","content":prompt}],
                temperature=0.1,
                max_tokens=1500,
                response_format={"type":"json_object"}
            )

            dados=json.loads(r.choices[0].message.content)

            if tema=="ANO":
                dados["resposta"]=re.sub("[^0-9]","",dados["resposta"])
                if len(dados["resposta"])!=4:
                    continue

                audit=auditar_carta_ano(dados)
                if not audit["valido"]:
                    registrar_log(f"Ano rejeitado:{audit['erros']}")
                    continue

            if verificar_similaridade(dados["resposta"]):
                continue

            st.session_state.used_answers.append(dados["resposta"])

            registrar_log(f"Aprovado:{dados['resposta']}")
            return dados

        except Exception as e:
            registrar_log(str(e))

    return None

# ================= UI =================

if not st.session_state.carta:

    if st.button("GERAR CARTA"):
        with st.spinner("Auditando..."):
            st.session_state.carta=obter_dados_carta()
            st.rerun()

else:

    c=st.session_state.carta

    st.subheader(c["tema"])

    if st.button("REVELAR"):
        st.success(c["resposta"])

    for d in c["dicas"]:
        st.write(d)

    if st.button("NOVA"):
        st.session_state.carta=None
        st.rerun()

with st.expander("LOG"):
    for l in st.session_state.logs[-20:]:
        st.code(l)
