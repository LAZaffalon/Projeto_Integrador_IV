from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from database import ensure_database, get_turma_data, list_turmas


BASE_DIR = Path(__file__).resolve().parent

st.set_page_config(
    page_title="Dashboard Educacional",
    page_icon="📚",
    layout="wide",
)

st.markdown(
    """
    <style>
        .stApp {
            background:
                radial-gradient(circle at top left, rgba(96, 165, 250, 0.18), transparent 25%),
                radial-gradient(circle at top right, rgba(168, 85, 247, 0.14), transparent 26%),
                linear-gradient(180deg, #f8fbff 0%, #eef4ff 100%);
        }
        .main .block-container {
            padding-top: 1.75rem;
            padding-bottom: 2.25rem;
            max-width: 1500px;
        }
        [data-testid="stMetric"] {
            background: linear-gradient(180deg, rgba(255,255,255,0.98), rgba(245,248,255,0.96));
            border: 1px solid rgba(148, 163, 184, 0.22);
            border-radius: 20px;
            padding: 1.1rem 1.2rem;
            box-shadow: 0 12px 30px rgba(15, 23, 42, 0.07), inset 0 1px 0 rgba(255,255,255,0.7);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        [data-testid="stMetric"]:hover {
            transform: translateY(-2px);
            box-shadow: 0 16px 36px rgba(59, 130, 246, 0.12);
        }
        [data-testid="stMetricLabel"] {
            color: #64748b !important;
            font-weight: 600;
            letter-spacing: 0.01em;
        }
        [data-testid="stMetricValue"] {
            color: #0f172a !important;
            font-weight: 800 !important;
            font-size: 1.8rem !important;
        }
        .app-header {
            position: relative;
            overflow: hidden;
            background: linear-gradient(135deg, #0b1120 0%, #111827 22%, #1d4ed8 100%);
            border-radius: 26px;
            padding: 1.9rem 1.9rem 1.7rem 1.9rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 18px 42px rgba(30, 64, 175, 0.2);
            border: 1px solid rgba(255,255,255,0.08);
        }
        .app-header::after {
            content: "";
            position: absolute;
            inset: -35% auto auto 58%;
            width: 240px;
            height: 240px;
            border-radius: 50%;
            background: rgba(255,255,255,0.06);
            filter: blur(10px);
        }
        .app-header h1 {
            position: relative;
            z-index: 1;
            color: white !important;
            margin: 0;
            font-size: 2.4rem;
            font-weight: 800;
            letter-spacing: -0.06em;
        }
        .app-header p {
            position: relative;
            z-index: 1;
            color: rgba(255,255,255,0.82);
            margin: 0.7rem 0 0 0;
            font-size: 1.02rem;
            line-height: 1.5;
            max-width: 820px;
        }
        .badge {
            position: relative;
            z-index: 1;
            display: inline-block;
            background: rgba(255,255,255,0.1);
            color: #e2e8f0;
            border: 1px solid rgba(255,255,255,0.18);
            border-radius: 999px;
            padding: 0.42rem 0.82rem;
            font-size: 0.72rem;
            font-weight: 800;
            letter-spacing: 0.08em;
            margin-bottom: 0.8rem;
            text-transform: uppercase;
            backdrop-filter: blur(8px);
        }
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, rgba(255,255,255,0.45), rgba(248,250,252,0.9));
            border-right: 1px solid rgba(148,163,184,0.2);
        }
        [data-testid="stSelectbox"], [data-testid="stMultiSelect"] {
            background: rgba(255,255,255,0.92);
            border: 1px solid rgba(148,163,184,0.24);
            border-radius: 12px;
            box-shadow: 0 10px 24px rgba(99, 102, 241, 0.04);
        }
        div[data-baseweb="tag"] {
            background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%);
            border: none;
            border-radius: 999px;
            color: white;
            padding: 0.2rem 0.52rem;
            margin: 0.1rem;
            box-shadow: 0 8px 18px rgba(99, 102, 241, 0.2);
        }
        div[data-baseweb="tag"] span {
            color: white !important;
            font-weight: 700;
        }
        .insight-box {
            background: linear-gradient(135deg, rgba(14, 116, 144, 0.08), rgba(59, 130, 246, 0.08));
            border: 1px solid rgba(59, 130, 246, 0.14);
            border-radius: 18px;
            padding: 1rem 1.2rem;
            margin-bottom: 1rem;
            box-shadow: inset 0 1px 0 rgba(255,255,255,0.6);
        }
        .modern-panel {
            background: linear-gradient(180deg, rgba(255,255,255,0.98), rgba(248,250,252,0.9));
            border: 1px solid rgba(148, 163, 184, 0.22);
            border-radius: 20px;
            padding: 1rem 1.15rem;
            box-shadow: 0 12px 30px rgba(15, 23, 42, 0.06);
            margin-top: 0.8rem;
        }
        .status-pill {
            display: inline-block;
            font-size: 0.7rem;
            font-weight: 800;
            letter-spacing: 0.06em;
            text-transform: uppercase;
            border-radius: 999px;
            padding: 0.38rem 0.8rem;
            margin-bottom: 0.7rem;
            background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
            color: #1d4ed8;
            box-shadow: inset 0 1px 0 rgba(255,255,255,0.8);
        }
        .status-pill.alert {
            background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
            color: #b91c1c;
        }
        .status-pill.success {
            background: linear-gradient(135deg, #dcfce7 0%, #bbf7d0 100%);
            color: #166534;
        }
        .stTabs [role="tablist"] {
            gap: 0.55rem;
            background: rgba(148, 163, 184, 0.08);
            padding: 0.35rem;
            border-radius: 16px;
            border: 1px solid rgba(148, 163, 184, 0.16);
            box-shadow: inset 0 1px 0 rgba(255,255,255,0.7);
        }
        .stTabs [role="tab"] {
            height: 46px;
            border-radius: 11px;
            background: rgba(255,255,255,0.62);
            color: #475569;
            font-weight: 700;
            border: 1px solid transparent;
            transition: all 0.2s ease;
        }
        .stTabs [role="tab"][aria-selected="true"] {
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
            color: white;
            box-shadow: 0 10px 22px rgba(15, 23, 42, 0.18);
            border: 1px solid rgba(255,255,255,0.12);
        }
        .stTabs [role="tab"]:not([aria-selected="true"]) {
            background: rgba(255,255,255,0.4);
            color: #475569;
        }
        [data-testid="stDataFrame"] {
            border-radius: 16px;
            overflow: hidden;
            border: 1px solid rgba(148, 163, 184, 0.18);
            box-shadow: 0 8px 20px rgba(15, 23, 42, 0.04);
        }
        .section-title {
            color: #0f172a;
            margin-bottom: 0.6rem;
        }
        .stButton > button {
            border-radius: 12px;
            font-weight: 700;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

ensure_database()
lista_turmas = list_turmas()

anos_disponiveis = []
for turma in lista_turmas:
    match = str(turma).strip()
    if "º" in match and "Ano" in match:
        numero = match.split("º", 1)[0].strip()
        if numero.isdigit():
            anos_disponiveis.append(int(numero))

anos_disponiveis = sorted(set(anos_disponiveis))

if len(anos_disponiveis) == 0:
    periodo_descritivo = "turmas disponíveis"
elif len(anos_disponiveis) == 1:
    periodo_descritivo = f"{anos_disponiveis[0]}º ano"
elif len(anos_disponiveis) == 2:
    periodo_descritivo = f"{anos_disponiveis[0]}º e {anos_disponiveis[1]}º ano"
else:
    anos_texto = ", ".join(f"{ano}º" for ano in anos_disponiveis[:-1])
    periodo_descritivo = f"{anos_texto} e {anos_disponiveis[-1]}º anos"

st.markdown(
    f"""
    <div class="app-header">
        <div class="badge">Dashboard educacional</div>
        <h1>📊 Performance Escolar</h1>
        <p>Análise descritiva das turmas do {periodo_descritivo}, com foco em engajamento, leitura e compreensão.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="insight-box">
        <strong>Visão estratégica</strong><br>
        Monitoramento pedagógico em tempo real, com foco em leitura, compreensão e risco de evasão de aprendizagem.
    </div>
    """,
    unsafe_allow_html=True,
)

serie_turma = st.selectbox("Selecione a turma", lista_turmas)
df = get_turma_data(serie_turma)

if df.empty:
    st.warning("Não foi possível carregar os dados da turma selecionada.")
    st.stop()

with st.sidebar:
    st.header("Filtros")
    st.caption("Ajuste a análise para entender melhor o desempenho da turma.")

    niveis_disponiveis = sorted(df["nivel"].dropna().astype(str).str.upper().unique().tolist())
    nivel_filtro = st.multiselect(
        "Nível de leitura",
        niveis_disponiveis,
        default=niveis_disponiveis,
        help="Selecione um ou mais níveis para comparar o desempenho dos alunos.",
    )

    filtro_status = st.radio(
        "Exibir alunos",
        options=["Todos", "Em risco", "Estáveis"],
        index=0,
        horizontal=True,
        help="Filtra a visão por situação pedagógica da turma.",
    )

    st.markdown("---")
    st.info("Os dados são carregados a partir do banco SQLite local do projeto.", icon="🗄️")

    df_filtrado = df[df["nivel"].astype(str).str.upper().isin(nivel_filtro)].copy() if nivel_filtro else df.copy()

    limiar_engajamento = 50
    limiar_compreensao = 50
    limiar_leituras = max(1, int(df_filtrado["total_de_leituras"].median()))

    risk_df = df_filtrado.copy()
    risk_df["em_risco"] = (
        (risk_df["engajamento_leitura"] < limiar_engajamento)
        | (risk_df["compreensao_textual"] < limiar_compreensao)
        | (risk_df["total_de_leituras"] < limiar_leituras)
    )
    risk_df["nivel_risco"] = "Alerta"
    risk_df.loc[~risk_df["em_risco"], "nivel_risco"] = "Estável"

    if filtro_status == "Em risco":
        df_filtrado = risk_df[risk_df["em_risco"]].copy()
    elif filtro_status == "Estáveis":
        df_filtrado = risk_df[~risk_df["em_risco"]].copy()
    else:
        df_filtrado = risk_df.copy()

media_engajamento = df_filtrado["engajamento_leitura"].mean()
media_compreensao = df_filtrado["compreensao_textual"].mean()
media_leituras = df_filtrado["total_de_leituras"].mean()
media_questoes = df_filtrado["questoes_respondidas"].mean()
qtd_alunos = len(df_filtrado)

alunos_em_risco = df_filtrado[df_filtrado["em_risco"]].copy().sort_values(
    ["engajamento_leitura", "compreensao_textual"], ascending=True
) if "em_risco" in df_filtrado.columns else pd.DataFrame()

if df_filtrado.empty:
    st.warning("Nenhum aluno atende aos filtros selecionados. Ajuste os critérios para visualizar a turma.")
    st.stop()

# Classificação de risco pedagógico
limiar_engajamento = 50
limiar_compreensao = 50
limiar_leituras = max(1, int(df["total_de_leituras"].median()))

if "em_risco" not in df_filtrado.columns:
    df_filtrado["em_risco"] = (
        (df_filtrado["engajamento_leitura"] < limiar_engajamento)
        | (df_filtrado["compreensao_textual"] < limiar_compreensao)
        | (df_filtrado["total_de_leituras"] < limiar_leituras)
    )
    df_filtrado["nivel_risco"] = "Alerta"
    df_filtrado.loc[~df_filtrado["em_risco"], "nivel_risco"] = "Estável"

alunos_em_risco = df_filtrado[df_filtrado["em_risco"]].copy().sort_values(
    ["engajamento_leitura", "compreensao_textual"], ascending=True
) if not df_filtrado.empty else pd.DataFrame()

st.markdown(
    """
    <div class="insight-box">
        <strong>Resumo executivo</strong><br>
        A visualização mostra o comportamento da turma em leitura, engajamento e compreensão, além de sinalizar alunos que podem necessitar de atenção pedagógica.
    </div>
    """,
    unsafe_allow_html=True,
)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Alunos", f"{qtd_alunos}")
col2.metric("Engajamento", f"{media_engajamento:.1f}%")
col3.metric("Compreensão", f"{media_compreensao:.1f}%")
col4.metric("Alunos em risco", f"{len(alunos_em_risco)}")

status_class = "status-pill alert" if len(alunos_em_risco) > 0 else "status-pill success"
status_label = "Atenção pedagógica" if len(alunos_em_risco) > 0 else "Turma estável"

st.markdown(
    f"""
    <div class="modern-panel">
        <div class="{status_class}">{status_label}</div>
        <div style="font-size: 1.1rem; font-weight: 600; color: #0f172a;">Resumo de acompanhamento</div>
        <div style="margin-top: 0.35rem; color: #475569;">A turma apresenta média de {media_engajamento:.1f}% de engajamento e {media_compreensao:.1f}% de compreensão, com {len(alunos_em_risco)} estudantes em atenção prioritária.</div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("### Interpretação rápida")
if media_engajamento >= 70:
    st.success("A turma apresenta um bom nível de engajamento, com tendência de participação ativa e continuidade das atividades.")
elif media_engajamento >= 50:
    st.info("A turma está em um patamar moderado de engajamento; há sinais positivos, mas ainda existe espaço para intensificar a participação.")
else:
    st.warning("O engajamento da turma está abaixo do esperado, sugerindo necessidade de reforço pedagógico e acompanhamento mais próximo.")

if media_compreensao >= 70:
    st.success("A compreensão dos conteúdos está acima do esperado, indicando que a maioria dos alunos consegue processar e responder de forma adequada.")
elif media_compreensao >= 50:
    st.info("A compreensão está em nível intermediário, sendo um ponto forte, mas com margem para aprofundamento no desenvolvimento da leitura.")
else:
    st.warning("A compreensão da turma está abaixo do patamar desejado, apontando necessidade de atenção diferenciada na leitura e interpretação textual.")

st.markdown("<div class='section-title'><h3>Visão geral da turma</h3></div>", unsafe_allow_html=True)

col_a, col_b = st.columns(2)
with col_a:
    nivel_counts = df_filtrado["nivel_numerico"].value_counts().sort_index()
    fig, ax = plt.subplots(figsize=(6, 4))
    colors = ["#4C78A8" if i == max(nivel_counts.index) else "#6BAED6" for i in nivel_counts.index]
    ax.bar(nivel_counts.index.astype(str), nivel_counts.values, color=colors, edgecolor="black", linewidth=0.5)
    ax.set_title("Distribuição por nível de leitura")
    ax.set_xlabel("Nível")
    ax.set_ylabel("Quantidade")
    ax.grid(axis="y", linestyle="--", alpha=0.3)
    st.pyplot(fig)

with col_b:
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.hist(df_filtrado["engajamento_leitura"], bins=10, color="#72B7B2", edgecolor="black")
    ax.axvline(limiar_engajamento, color="#d62728", linestyle="--", linewidth=2, label="Limite de risco")
    ax.set_title("Distribuição do engajamento")
    ax.set_xlabel("Engajamento (%)")
    ax.set_ylabel("Frequência")
    ax.grid(axis="y", linestyle="--", alpha=0.3)
    ax.legend()
    st.pyplot(fig)

st.markdown("### Alunos em risco")
if alunos_em_risco.empty:
    st.markdown(
        """
        <div class="modern-panel">
            <div class="status-pill success">Sem alertas</div>
            <div style="color: #0f172a; font-weight: 600;">Nenhum aluno foi identificado com indicadores de risco.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    risco_display = alunos_em_risco[
        [
            "nome_do_estudante",
            "nivel",
            "engajamento_leitura",
            "compreensao_textual",
            "total_de_leituras",
            "questoes_respondidas",
        ]
    ].copy()
    risco_display["engajamento_leitura"] = risco_display["engajamento_leitura"].round(2)
    risco_display["compreensao_textual"] = risco_display["compreensao_textual"].round(2)
    risco_display["status"] = "Atenção"
    st.dataframe(risco_display, use_container_width=True)
    st.caption("Indicadores de risco calculados a partir de engajamento, compreensão e volume de leitura.")

st.markdown("### Dados da turma")

data_display = df_filtrado[
    [
        "nome_do_estudante",
        "nivel",
        "nivel_numerico",
        "total_de_leituras",
        "tempo_de_leitura_minutos",
        "questoes_respondidas",
        "questoes_aprovadas",
        "compreensao_textual",
        "engajamento_leitura",
    ]
].copy()

for col in ["total_de_leituras", "tempo_de_leitura_minutos", "questoes_respondidas", "questoes_aprovadas", "compreensao_textual", "engajamento_leitura"]:
    if col in data_display.columns:
        data_display[col] = data_display[col].round(2)

st.dataframe(data_display.head(15), use_container_width=True)

st.markdown("---")

tab1, tab2, tab3 = st.tabs(["Desempenho por aluno", "Comparativos", "Estatísticas"])

with tab1:
    st.markdown("### Ranking dos alunos")
    ranking = df_filtrado.sort_values(["engajamento_leitura", "compreensao_textual"], ascending=False).reset_index(drop=True)
    ranking["posicao"] = range(1, len(ranking) + 1)

    ranking_display = ranking[
        [
            "posicao",
            "nome_do_estudante",
            "nivel",
            "engajamento_leitura",
            "compreensao_textual",
            "total_de_leituras",
        ]
    ].copy()
    ranking_display["engajamento_leitura"] = ranking_display["engajamento_leitura"].round(2)
    ranking_display["compreensao_textual"] = ranking_display["compreensao_textual"].round(2)
    st.dataframe(ranking_display, use_container_width=True)

    fig, ax = plt.subplots(figsize=(10, 5))
    cores = ["#1f77b4" if value >= limiar_engajamento else "#d62728" for value in ranking["engajamento_leitura"].head(10)]
    ax.barh(ranking["nome_do_estudante"].head(10)[::-1], ranking["engajamento_leitura"].head(10)[::-1], color=cores[::-1])
    ax.set_title("Top 10 alunos por engajamento")
    ax.set_xlabel("Engajamento (%)")
    ax.set_ylabel("Aluno")
    ax.axvline(limiar_engajamento, color="#d62728", linestyle="--", linewidth=1.5, label="Limite de risco")
    ax.legend()
    st.pyplot(fig)

with tab2:
    col_a, col_b = st.columns(2)

    with col_a:
        fig, ax = plt.subplots(figsize=(6, 4))
        scatter_colors = ["#2ca02c" if not row["em_risco"] else "#d62728" for _, row in risk_df.iterrows()]
        ax.scatter(
            risk_df["compreensao_textual"],
            risk_df["engajamento_leitura"],
            alpha=0.8,
            c=scatter_colors,
            s=80,
            edgecolors="black",
            linewidth=0.4,
        )
        ax.axhline(limiar_engajamento, color="#d62728", linestyle="--", linewidth=1.4, alpha=0.8)
        ax.axvline(limiar_compreensao, color="#d62728", linestyle="--", linewidth=1.4, alpha=0.8)
        ax.set_title("Relação entre compreensão e engajamento")
        ax.set_xlabel("Compreensão textual (%)")
        ax.set_ylabel("Engajamento (%)")
        ax.grid(True, linestyle="--", alpha=0.3)
        st.pyplot(fig)

    with col_b:
        fig, ax = plt.subplots(figsize=(6, 4))
        desempenho = df_filtrado.groupby("nivel", as_index=False)["compreensao_textual"].mean()
        ax.bar(desempenho["nivel"], desempenho["compreensao_textual"], color="#E45756")
        ax.set_title("Média de compreensão por nível")
        ax.set_xlabel("Nível")
        ax.set_ylabel("Compreensão média (%)")
        ax.grid(axis="y", linestyle="--", alpha=0.3)
        st.pyplot(fig)

with tab3:
    st.markdown("### Estatísticas resumidas")
    resumo = df_filtrado[
        [
            "total_de_leituras",
            "tempo_de_leitura_minutos",
            "questoes_respondidas",
            "compreensao_textual",
            "engajamento_leitura",
        ]
    ].describe().round(2)
    st.write(resumo)

st.markdown("---")
st.caption("Aplicativo desenvolvido para análise educacional com Streamlit.")