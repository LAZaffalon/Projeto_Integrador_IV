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
            background: linear-gradient(180deg, #f4f7ff 0%, #eef4ff 100%);
        }
        .main .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        div[data-testid="stMetric"] {
            background: rgba(255, 255, 255, 0.85);
            border: 1px solid #dfe8ff;
            border-radius: 18px;
            padding: 1rem 1.25rem;
            box-shadow: 0 8px 20px rgba(46, 83, 184, 0.08);
        }
        .app-header {
            background: linear-gradient(135deg, #0f172a 0%, #1d4ed8 100%);
            border-radius: 20px;
            padding: 1.5rem 1.75rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 10px 28px rgba(29, 78, 216, 0.18);
        }
        .app-header h1 {
            color: white !important;
            margin: 0;
            font-size: 2.2rem;
            letter-spacing: -0.04em;
        }
        .app-header p {
            color: rgba(255,255,255,0.8);
            margin: 0.5rem 0 0 0;
            font-size: 1rem;
        }
        .badge {
            display: inline-block;
            background: rgba(255,255,255,0.12);
            color: #ffffff;
            border: 1px solid rgba(255,255,255,0.25);
            border-radius: 999px;
            padding: 0.35rem 0.7rem;
            font-size: 0.76rem;
            font-weight: 600;
            margin-bottom: 0.7rem;
        }
        [data-testid="stSidebar"] {
            background: rgba(15, 23, 42, 0.03);
        }
        [data-testid="stMultiSelect"] {
            background: rgba(255,255,255,0.9);
            border: 1px solid #dfe8ff;
            border-radius: 14px;
            padding: 0.2rem 0.45rem;
            box-shadow: 0 8px 18px rgba(99, 102, 241, 0.07);
        }
        div[data-baseweb="tag"] {
            background: linear-gradient(135deg, #ff7a59 0%, #ff5f6d 100%);
            border: none;
            border-radius: 999px;
            color: white;
            padding: 0.2rem 0.5rem;
            margin: 0.15rem;
            box-shadow: 0 4px 10px rgba(255, 95, 109, 0.18);
        }
        div[data-baseweb="tag"] span {
            color: white !important;
            font-weight: 600;
        }
        div[data-baseweb="tag"] button {
            color: white !important;
            opacity: 0.9;
        }
        .stTabs [role="tablist"] {
            gap: 0.5rem;
        }
        .stTabs [role="tab"] {
            height: 42px;
            border-radius: 10px;
            background: rgba(148, 163, 184, 0.08);
            color: #334155;
            font-weight: 600;
        }
        .stTabs [role="tab"][aria-selected="true"] {
            background: linear-gradient(135deg, #1d4ed8 0%, #2563eb 100%);
            color: white;
        }
        [data-testid="stDataFrame"] {
            border-radius: 14px;
            overflow: hidden;
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
        <div class="badge">Dashboard Educacional</div>
        <h1>📊 Performance Escolar</h1>
        <p>Análise descritiva das turmas do {periodo_descritivo} com visão integrada dos indicadores.</p>
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
    st.markdown("<div style='margin-bottom: 1rem; color: #475569;'>Ajuste os indicadores para comparar o desempenho da turma.</div>", unsafe_allow_html=True)
    nivel_filtro = st.multiselect(
        "Nível de leitura",
        sorted(df["nivel_numerico"].dropna().unique().tolist()),
        default=sorted(df["nivel_numerico"].dropna().unique().tolist()),
    )

    if nivel_filtro:
        df_filtrado = df[df["nivel_numerico"].isin(nivel_filtro)].copy()
    else:
        df_filtrado = df.copy()

    st.markdown("---")
    st.info("Os dados são carregados a partir do banco SQLite local do projeto.", icon="🗄️")

media_engajamento = df_filtrado["engajamento_leitura"].mean()
media_compreensao = df_filtrado["compreensao_textual"].mean()
media_leituras = df_filtrado["total_de_leituras"].mean()
media_questoes = df_filtrado["questoes_respondidas"].mean()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Engajamento médio", f"{media_engajamento:.1f}%")
col2.metric("Compreensão média", f"{media_compreensao:.1f}%")
col3.metric("Leituras por aluno", f"{media_leituras:.0f}")
col4.metric("Questões respondidas", f"{media_questoes:.0f}")

tab1, tab2, tab3 = st.tabs(["Visão geral", "Desempenho por aluno", "Comparativos"])

with tab1:
    col_left, col_right = st.columns(2)

    with col_left:
        nivel_counts = df_filtrado["nivel_numerico"].value_counts().sort_index()
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.bar(nivel_counts.index.astype(str), nivel_counts.values, color="#4C78A8")
        ax.set_title("Distribuição por nível de leitura")
        ax.set_xlabel("Nível")
        ax.set_ylabel("Quantidade")
        ax.grid(axis="y", linestyle="--", alpha=0.3)
        st.pyplot(fig)

    with col_right:
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.hist(df_filtrado["engajamento_leitura"], bins=10, color="#72B7B2", edgecolor="black")
        ax.set_title("Distribuição do engajamento")
        ax.set_xlabel("Engajamento (%)")
        ax.set_ylabel("Frequência")
        ax.grid(axis="y", linestyle="--", alpha=0.3)
        st.pyplot(fig)

    st.markdown("### Resumo da turma")
    st.dataframe(
        df_filtrado[
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
        ].head(15),
        use_container_width=True,
    )

with tab2:
    st.markdown("### Ranking dos alunos")
    ranking = df_filtrado.sort_values(
        ["engajamento_leitura", "compreensao_textual"], ascending=False
    ).reset_index(drop=True)
    ranking["posicao"] = range(1, len(ranking) + 1)
    st.dataframe(
        ranking[
            [
                "posicao",
                "nome_do_estudante",
                "nivel",
                "engajamento_leitura",
                "compreensao_textual",
                "total_de_leituras",
            ]
        ],
        use_container_width=True,
    )

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.barh(
        ranking["nome_do_estudante"].head(10)[::-1],
        ranking["engajamento_leitura"].head(10)[::-1],
        color="#F58518",
    )
    ax.set_title("Top 10 alunos por engajamento")
    ax.set_xlabel("Engajamento (%)")
    ax.set_ylabel("Aluno")
    st.pyplot(fig)

with tab3:
    col_a, col_b = st.columns(2)

    with col_a:
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.scatter(
            df_filtrado["compreensao_textual"],
            df_filtrado["engajamento_leitura"],
            alpha=0.8,
            color="#54A24B",
        )
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

    st.markdown("### Estatísticas resumidas")
    st.write(
        df_filtrado[
            [
                "total_de_leituras",
                "tempo_de_leitura_minutos",
                "questoes_respondidas",
                "compreensao_textual",
                "engajamento_leitura",
            ]
        ].describe().round(2)
    )

st.markdown("---")
st.caption("Aplicativo desenvolvido para análise educacional com Streamlit.")