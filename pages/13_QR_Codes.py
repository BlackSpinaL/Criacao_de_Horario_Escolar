import streamlit as st
import pandas as pd
from sqlalchemy import text
from core.db import get_engine
from core.qr_code import (
    gerar_qr_bytes,
    gerar_qr_com_legenda,
    link_disponibilidade,
    link_meu_horario,
)

st.set_page_config(page_title="QR Codes", page_icon="📱", layout="wide")
st.title("📱 QR Codes dos Professores")
st.caption(
    "Gere QR Codes para os professores acessarem as páginas do sistema "
    "pelo celular (sem digitar link)."
)

engine = get_engine()

# ---------- Ano letivo ----------
with engine.connect() as conn:
    ano_row = conn.execute(
        text("SELECT id, ano FROM anos_letivos WHERE ativo = TRUE LIMIT 1")
    ).first()

if ano_row is None:
    st.warning("Rode o seed 2026 primeiro.")
    st.stop()

ano_id = ano_row.id

# ---------- Professores ----------
with engine.connect() as conn:
    profs = pd.read_sql(text("""
        SELECT id, nome, numero_pm FROM professores ORDER BY nome
    """), conn)

if profs.empty:
    st.warning("Nenhum professor cadastrado ainda.")
    st.stop()

# =====================================================================
# CONFIGURAÇÃO
# =====================================================================
col_c1, col_c2 = st.columns([2, 2])

with col_c1:
    tipo_link = st.selectbox(
        "Tipo de página",
        [
            "🚫 Minha Disponibilidade (marcar horários)",
            "📅 Meu Horário (ver grade)",
        ],
    )

with col_c2:
    formato = st.selectbox(
        "Formato",
        ["QR simples (só o código)", "QR com legenda (para impressão)"],
    )

st.divider()

# =====================================================================
# PREVIEW INDIVIDUAL
# =====================================================================
st.subheader("👁️ Visualizar e baixar um QR Code")

prof_sel = st.selectbox(
    "Escolha um professor",
    profs["id"].tolist(),
    format_func=lambda x: (
        f"{profs.loc[profs['id'] == x, 'nome'].iloc[0]}"
        + (f" (Nº PM {profs.loc[profs['id'] == x, 'numero_pm'].iloc[0]})"
           if pd.notna(profs.loc[profs['id'] == x, 'numero_pm'].iloc[0]) else "")
    ),
)

prof_row = profs.loc[profs["id"] == prof_sel].iloc[0]
nome = prof_row["nome"]
num_pm = prof_row["numero_pm"] if pd.notna(prof_row["numero_pm"]) else None

# Gera link
if "Disponibilidade" in tipo_link:
    link = link_disponibilidade(nome_professor=nome, numero_pm=num_pm)
    titulo_qr = nome
    sub_qr = f"Nº PM: {num_pm}" if num_pm else "Disponibilidade"
else:
    link = link_meu_horario(nome_professor=nome, numero_pm=num_pm)
    titulo_qr = nome
    sub_qr = f"Nº PM: {num_pm}" if num_pm else "Meu Horário"

st.markdown(f"**Link gerado:**")
st.code(link, language=None)

col_q1, col_q2 = st.columns([1, 1])

with col_q1:
    st.markdown("**QR Code:**")
    if formato == "QR simples (só o código)":
        img_bytes = gerar_qr_bytes(link, com_cor=True)
    else:
        img_bytes = gerar_qr_com_legenda(link, titulo_qr, sub_qr)

    st.image(img_bytes, width=320)

with col_q2:
    st.markdown("**Downloads:**")
    nome_arquivo = nome.replace(" ", "_").replace("/", "-")

    st.download_button(
        "⬇️ Baixar QR (PNG)",
        img_bytes,
        f"QR_{nome_arquivo}.png",
        "image/png",
        use_container_width=True,
    )

    # QR simples sempre disponível
    img_simples = gerar_qr_bytes(link, com_cor=True)
    st.download_button(
        "⬇️ Baixar QR simples (PNG)",
        img_simples,
        f"QR_{nome_arquivo}_simples.png",
        "image/png",
        use_container_width=True,
    )

st.divider()

# =====================================================================
# LISTA COMPLETA
# =====================================================================
st.subheader("📋 Todos os professores")
st.caption(
    "Clique em cada card para baixar o QR Code individual. "
    "Para impressão em lote, use o botão abaixo (gera uma página com "
    "todos os QRs para imprimir e recortar)."
)

# Filtro
filtro = st.text_input("🔍 Filtrar por nome", placeholder="Ex: João")

df_filt = profs.copy()
if filtro:
    df_filt = df_filt[df_filt["nome"].str.contains(filtro, case=False, na=False)]

# Grid de cards (4 colunas)
COLS = 4
for i in range(0, len(df_filt), COLS):
    cols = st.columns(COLS)
    for j, (_, row) in enumerate(df_filt.iloc[i:i+COLS].iterrows()):
        with cols[j]:
            nome_p = row["nome"]
            pm_p = row["numero_pm"] if pd.notna(row["numero_pm"]) else None

            if "Disponibilidade" in tipo_link:
                link_p = link_disponibilidade(nome_professor=nome_p, numero_pm=pm_p)
            else:
                link_p = link_meu_horario(nome_professor=nome_p, numero_pm=pm_p)

            img_p = gerar_qr_bytes(link_p, com_cor=True)
            st.image(img_p, use_container_width=True)

            st.markdown(
                f"**{nome_p[:22]}{'...' if len(nome_p) > 22 else ''}**"
            )
            if pm_p:
                st.caption(f"Nº PM: {pm_p}")

            st.download_button(
                "⬇️ Baixar",
                img_p,
                f"QR_{nome_p.replace(' ', '_')}.png",
                "image/png",
                key=f"dl_{row['id']}",
                use_container_width=True,
            )

st.divider()

# =====================================================================
# GERAR FOLHA DE IMPRESSÃO (HTML)
# =====================================================================
st.subheader("🖨️ Gerar folha para impressão")
st.caption(
    "Gera uma página HTML com todos os QRs prontos para imprimir em A4 "
    "(~6 por página). Recorte e distribua aos professores."
)

with st.expander("Clique para gerar a folha"):
    st.markdown("**Filtrar professores incluídos:**")

    filtro_imp = st.text_input(
        "Filtrar por nome (opcional)",
        placeholder="Deixe vazio para incluir todos",
        key="filtro_imp",
    )

    incluir_todos = not filtro_imp

    df_imp = profs.copy()
    if filtro_imp:
        df_imp = df_imp[df_imp["nome"].str.contains(filtro_imp, case=False, na=False)]

    st.caption(f"**{len(df_imp)} professor(es)** serão incluídos")

    if st.button("🖨️ Gerar folha HTML", type="primary"):
        # Monta HTML com os QRs em base64
        import base64

        html_partes = []
        html_partes.append("""
        <!DOCTYPE html>
        <html lang="pt-BR">
        <head>
        <meta charset="UTF-8">
        <title>QR Codes - Professores</title>
        <style>
            @page { size: A4; margin: 10mm; }
            body { font-family: Arial, sans-serif; margin: 0; padding: 0; }
            .grid { display: grid; grid-template-columns: repeat(2, 1fr);
                    gap: 8mm; }
            .card {
                border: 2px solid #1F4E78;
                border-radius: 8px;
                padding: 8px;
                text-align: center;
                page-break-inside: avoid;
                background: #FFF;
            }
            .card img { width: 100%; max-width: 240px; height: auto; }
            .titulo { font-weight: bold; color: #1F4E78;
                      font-size: 14px; margin: 4px 0 2px 0; }
            .sub { color: #666; font-size: 11px; margin-bottom: 4px; }
            .instrucao { color: #999; font-size: 9px; margin-top: 4px; }
            .header { text-align: center; margin-bottom: 6mm; }
            .header h1 { color: #1F4E78; font-size: 18px; margin: 0; }
            .header p { color: #666; font-size: 11px; margin: 4px 0; }
            @media print { .no-print { display: none; } }
        </style>
        </head>
        <body>
        <div class="header">
            <h1>📱 QR Codes dos Professores</h1>
            <p>CTPM/Lavras — Sistema de Grade Horária</p>
            <p style="font-size:10px;">Aponte a câmera do celular para o QR Code
               e acesse a página do sistema</p>
        </div>
        <div class="grid">
        """)

        for _, row in df_imp.iterrows():
            nome_p = row["nome"]
            pm_p = row["numero_pm"] if pd.notna(row["numero_pm"]) else None

            if "Disponibilidade" in tipo_link:
                link_p = link_disponibilidade(nome_professor=nome_p, numero_pm=pm_p)
                pagina_nome = "Minha Disponibilidade"
            else:
                link_p = link_meu_horario(nome_professor=nome_p, numero_pm=pm_p)
                pagina_nome = "Meu Horário"

            img_p = gerar_qr_bytes(link_p, com_cor=True)
            b64 = base64.b64encode(img_p).decode("ascii")

            sub = f"Nº PM: {pm_p}" if pm_p else pagina_nome

            html_partes.append(f"""
            <div class="card">
                <img src="data:image/png;base64,{b64}" alt="QR {nome_p}">
                <div class="titulo">{nome_p}</div>
                <div class="sub">{sub}</div>
                <div class="instrucao">Aponte a câmera para acessar</div>
            </div>
            """)

        html_partes.append("""
        </div>
        </body>
        </html>
        """)

        html_completo = "".join(html_partes).encode("utf-8")

        st.success(
            f"✅ Folha gerada com **{len(df_imp)} QR Codes**. "
            "Baixe o arquivo abaixo e abra no navegador. Depois, "
            "aperte **Ctrl+P** (ou Cmd+P) para imprimir em A4."
        )

        st.download_button(
            "⬇️ Baixar folha (HTML)",
            html_completo,
            "QR_Codes_Professores.html",
            "text/html",
            use_container_width=True,
        )

        st.info(
            "💡 **Dica:** abra o arquivo HTML no navegador e use "
            "**Salvar como PDF** se preferir arquivo em vez de imprimir direto."
        )

st.divider()

# =====================================================================
# INFORMAÇÕES
# =====================================================================
with st.expander("ℹ️ Como usar os QR Codes"):
    st.markdown(f"""
    ### Fluxo recomendado

    1. **Escolha o tipo de página** no topo (Disponibilidade ou Horário)
    2. **Gere a folha HTML** com todos os professores
    3. **Imprima em A4** (idealmente colorida, mas funciona em P&B)
    4. **Recorte** cada cartão
    5. **Distribua** aos professores (ou cole no mural da sala dos professores)
    6. Professor aponta a **câmera do celular** → abre o sistema direto

    ### Vantagens

    - ✅ Sem digitar link ou senha
    - ✅ Funciona em qualquer celular com câmera (Android e iPhone)
    - ✅ Professor não precisa instalar nada
    - ✅ Ideal para distribuir no início do ano letivo

    ### Observação

    Se um professor **não tem Nº PM** cadastrado, o QR Code usa o
    **nome dele** como identificador. Recomendamos cadastrar o Nº PM
    para evitar confusão de nomes iguais.
    """)
