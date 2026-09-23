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

st.title("📊 Dashboard de Performance Escolar")
st.caption("Análise descritiva das turmas de 2º e 5º ano")

ensure_database()
lista_turmas = list_turmas()

serie_turma = st.selectbox("Selecione a turma", lista_turmas)
df = get_turma_data(serie_turma)

if df.empty:
    st.warning("Não foi possível carregar os dados da turma selecionada.")
    st.stop()

with st.sidebar:
    st.header("Filtros")
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
    st.write("Fonte dos dados: banco SQLite local do projeto.")

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
    st.dataframe(df_filtrado[[
        "nome_do_estudante",
        "nivel",
        "nivel_numerico",
        "total_de_leituras",
        "tempo_de_leitura_minutos",
        "questoes_respondidas",
        "questoes_aprovadas",
        "compreensao_textual",
        "engajamento_leitura",
    ]].head(15), use_container_width=True)

with tab2:
    st.markdown("### Ranking dos alunos")
    ranking = df_filtrado.sort_values(
        ["engajamento_leitura", "compreensao_textual"], ascending=False
    ).reset_index(drop=True)
    ranking["posicao"] = range(1, len(ranking) + 1)
    st.dataframe(
        ranking[["posicao", "nome_do_estudante", "nivel", "engajamento_leitura", "compreensao_textual", "total_de_leituras"]],
        use_container_width=True,
    )

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.barh(ranking["nome_do_estudante"].head(10)[::-1], ranking["engajamento_leitura"].head(10)[::-1], color="#F58518")
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
    st.write(df_filtrado[["total_de_leituras", "tempo_de_leitura_minutos", "questoes_respondidas", "compreensao_textual", "engajamento_leitura"]].describe().round(2))

st.markdown("---")
st.caption("Aplicativo desenvolvido para análise educacional com Streamlit.")