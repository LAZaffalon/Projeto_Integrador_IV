import re
import sqlite3
from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
DATASET_DIR = BASE_DIR / "dataset_clear"
DB_PATH = BASE_DIR / "educacao.db"

NUMERIC_COLUMNS = [
    "leituras_em_andamento",
    "leituras_concluidas",
    "total_de_leituras",
    "tempo_de_leitura_minutos",
    "questoes_respondidas",
    "questoes_aprovadas",
    "nivel_numerico",
    "livros_escutados",
    "tempo_de_escuta_minutos",
    "compreensao_textual",
    "engajamento_leitura",
]

COLUMN_ALIASES = {
    "nome_do_estudante": ["nome do estudante", "nome_do_estudante"],
    "leituras_em_andamento": ["leituras em andamento", "leituras_em_andamento"],
    "leituras_concluidas": ["leituras concluídas", "leituras_concluidas", "leituras concluídas "],
    "total_de_leituras": ["total de leituras", "total_de_leituras"],
    "tempo_de_leitura_minutos": ["tempo de leitura", "tempo_de_leitura_minutos"],
    "questoes_respondidas": ["questões respondidas", "questoes_respondidas"],
    "questoes_aprovadas": ["questões aprovadas", "questoes_aprovadas"],
    "nivel": ["nível", "nivel"],
    "livros_escutados": ["livros escutados", "livros_escutados"],
    "tempo_de_escuta": ["tempo de escuta", "tempo_de_escuta"],
}


def _infer_serie_name(file_path: Path) -> str:
    nome = file_path.stem.lower().replace("turma_", "").replace("_", " ")
    match = re.search(r"(\d+)\s*ano", nome)
    if match:
        numero = match.group(1)
        return f"{numero}º Ano"
    return nome.title()


def _sum_duration_to_minutos(valor):
    if pd.isna(valor):
        return 0.0
    texto = str(valor).strip().lower()
    if not texto or texto == "nan":
        return 0.0
    if texto.endswith("s") and "h" not in texto and "m" not in texto:
        return float(texto.replace("s", "")) / 60
    if re.search(r"\d", texto):
        horas = re.search(r"(\d+)h", texto)
        minutos = re.search(r"(\d+)m", texto)
        segundos = re.search(r"(\d+)s", texto)
        total = 0.0
        if horas:
            total += int(horas.group(1)) * 60
        if minutos:
            total += int(minutos.group(1))
        if segundos:
            total += int(segundos.group(1)) / 60
        return total
    try:
        return float(texto) / 60
    except ValueError:
        return 0.0


def _read_dataset(file_path: Path) -> pd.DataFrame:
    if file_path.suffix.lower() == ".csv":
        return pd.read_csv(file_path)
    if file_path.suffix.lower() in {".xlsx", ".xls"}:
        return pd.read_excel(file_path)
    raise ValueError(f"Formato não suportado: {file_path.suffix}")


def _discover_dataset_files() -> list[Path]:
    if not DATASET_DIR.exists():
        return []
    extensoes = {".csv", ".xlsx", ".xls"}
    return sorted(
        [arquivo for arquivo in DATASET_DIR.iterdir() if arquivo.is_file() and arquivo.suffix.lower() in extensoes],
        key=lambda item: item.name.lower(),
    )


def _normalizar_dataframe(df: pd.DataFrame, serie: str) -> pd.DataFrame:
    dados = df.copy()
    dados.columns = [str(col).strip().lower() for col in dados.columns]

    for alvo, possiveis in COLUMN_ALIASES.items():
        for nome in possiveis:
            if nome in dados.columns:
                dados = dados.rename(columns={nome: alvo})
                break

    if "nome_do_estudante" in dados.columns:
        dados["nome_do_estudante"] = [f"Aluno_{i:02d}" for i in range(1, len(dados) + 1)]
    else:
        dados["nome_do_estudante"] = [f"Aluno_{i:02d}" for i in range(1, len(dados) + 1)]

    if "turma" not in dados.columns:
        match = re.search(r"-(\s*[A-Z])\s*-\s*\d{4}", str(df.columns))
        turma = match.group(1).strip() if match else "A"
        dados["turma"] = turma

    if "periodo" not in dados.columns:
        nome_arquivo = str(serie).upper()
        dados["periodo"] = "tarde" if "TARDE" in nome_arquivo else "manha"

    if "tempo_de_leitura_minutos" in dados.columns:
        dados["tempo_de_leitura_minutos"] = pd.to_numeric(dados["tempo_de_leitura_minutos"], errors="coerce")
        if dados["tempo_de_leitura_minutos"].max() and dados["tempo_de_leitura_minutos"].max() > 10000:
            dados["tempo_de_leitura_minutos"] = dados["tempo_de_leitura_minutos"] / 60
    elif "tempo de leitura" in dados.columns:
        dados["tempo_de_leitura_minutos"] = pd.to_numeric(dados["tempo de leitura"], errors="coerce")
        if dados["tempo_de_leitura_minutos"].max() and dados["tempo_de_leitura_minutos"].max() > 10000:
            dados["tempo_de_leitura_minutos"] = dados["tempo_de_leitura_minutos"] / 60
    elif "tempo_de_leitura" in dados.columns:
        dados["tempo_de_leitura_minutos"] = pd.to_numeric(dados["tempo_de_leitura"], errors="coerce")
    else:
        dados["tempo_de_leitura_minutos"] = 0.0

    if "tempo_de_escuta" in dados.columns:
        dados["tempo_de_escuta_minutos"] = dados["tempo_de_escuta"].apply(_sum_duration_to_minutos)
    else:
        dados["tempo_de_escuta_minutos"] = 0.0

    if "nivel" in dados.columns:
        dados["nivel"] = dados["nivel"].astype(str).str.upper()
    else:
        dados["nivel"] = "C"

    if "nivel_numerico" not in dados.columns:
        mapa_nivel = {"A": 1, "B": 2, "C": 3, "D": 4, "E": 5, "N": 3}
        dados["nivel_numerico"] = dados["nivel"].map(mapa_nivel).fillna(3)

    if "questoes_respondidas" not in dados.columns:
        dados["questoes_respondidas"] = 0
    if "questoes_aprovadas" not in dados.columns:
        dados["questoes_aprovadas"] = 0
    if "leituras_em_andamento" not in dados.columns:
        dados["leituras_em_andamento"] = 0
    if "leituras_concluidas" not in dados.columns:
        dados["leituras_concluidas"] = 0
    if "total_de_leituras" not in dados.columns:
        dados["total_de_leituras"] = dados["leituras_concluidas"] + dados["leituras_em_andamento"]
    if "livros_escutados" not in dados.columns:
        dados["livros_escutados"] = 0

    if "compreensao_textual" not in dados.columns:
        dados["compreensao_textual"] = (dados["leituras_concluidas"] / dados["total_de_leituras"].replace(0, pd.NA)) * 100
        dados["compreensao_textual"] = dados["compreensao_textual"].fillna(0)

    if "engajamento_leitura" not in dados.columns:
        denominador = dados["questoes_respondidas"].replace(0, pd.NA)
        dados["engajamento_leitura"] = (dados["questoes_aprovadas"] / denominador) * 100
        dados["engajamento_leitura"] = dados["engajamento_leitura"].fillna(0)

    for coluna in NUMERIC_COLUMNS:
        if coluna in dados.columns:
            dados[coluna] = pd.to_numeric(dados[coluna], errors="coerce").fillna(0)

    dados["serie"] = serie
    return dados


def ensure_database() -> str:
    """Cria e popula o banco SQLite a partir de todos os arquivos de dados do projeto."""
    frames = []

    for caminho in _discover_dataset_files():
        serie = _infer_serie_name(caminho)
        df = _read_dataset(caminho)
        frames.append(_normalizar_dataframe(df, serie))

    conn = sqlite3.connect(DB_PATH)
    try:
        if frames:
            dados_combinados = pd.concat(frames, ignore_index=True)
            dados_combinados.to_sql("alunos", conn, if_exists="replace", index=False)
        else:
            conn.execute("CREATE TABLE IF NOT EXISTS alunos (serie TEXT)")
    finally:
        conn.close()

    return str(DB_PATH)


def list_turmas() -> list[str]:
    ensure_database()
    conn = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql_query("SELECT DISTINCT serie FROM alunos ORDER BY serie", conn)
    finally:
        conn.close()

    return df["serie"].astype(str).tolist() if not df.empty else []


def get_turma_data(serie: str) -> pd.DataFrame:
    ensure_database()
    conn = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql_query(
            "SELECT * FROM alunos WHERE serie = ? ORDER BY nome_do_estudante",
            conn,
            params=(serie,),
        )
    finally:
        conn.close()

    for coluna in NUMERIC_COLUMNS:
        if coluna in df.columns:
            df[coluna] = pd.to_numeric(df[coluna], errors="coerce")

    return df
