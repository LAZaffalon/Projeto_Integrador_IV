import re
import sqlite3
from datetime import datetime
from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
DATASET_DIR = BASE_DIR / "dataset_clear"
UPLOADS_DIR = BASE_DIR / "uploads"
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
    extensoes = {".csv", ".xlsx", ".xls"}
    pastas = [DATASET_DIR]
    if UPLOADS_DIR.exists():
        pastas.append(UPLOADS_DIR)

    arquivos = []
    for pasta in pastas:
        if not pasta.exists():
            continue
        arquivos.extend(
            arquivo
            for arquivo in pasta.iterdir()
            if arquivo.is_file() and arquivo.suffix.lower() in extensoes
        )

    series_com_csv = {
        _infer_serie_name(arquivo)
        for arquivo in arquivos
        if arquivo.suffix.lower() == ".csv"
    }
    arquivos_preferenciais = [
        arquivo
        for arquivo in arquivos
        if arquivo.suffix.lower() == ".csv"
        or _infer_serie_name(arquivo) not in series_com_csv
    ]

    return sorted(arquivos_preferenciais, key=lambda item: item.name.lower())


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


def _normalizar_nome_coluna(coluna: str) -> str:
    texto = str(coluna).strip().lower()
    texto = texto.replace("_", " ")
    texto = texto.replace("-", " ")
    texto = texto.replace("/", " ")
    texto = "".join(
        ch for ch in texto if ch.isalnum() or ch.isspace()
    ).strip()
    return " ".join(texto.split())


def validate_uploaded_csv(dataframe) -> tuple[bool, str, pd.DataFrame]:
    """Valida um CSV do usuário final e retorna o DataFrame padronizado."""
    if dataframe is None:
        return False, "Nenhum arquivo foi enviado.", pd.DataFrame()

    if hasattr(dataframe, "read"):
        try:
            dataframe.seek(0)
            df = pd.read_csv(dataframe)
        except Exception as exc:  # pragma: no cover - dependente do arquivo
            return False, f"Não foi possível ler o arquivo: {exc}", pd.DataFrame()
    elif isinstance(dataframe, (str, Path)):
        try:
            df = pd.read_csv(dataframe)
        except Exception as exc:  # pragma: no cover - dependente do arquivo
            return False, f"Não foi possível ler o arquivo: {exc}", pd.DataFrame()
    elif isinstance(dataframe, dict):
        df = pd.DataFrame(dataframe)
    else:
        df = dataframe.copy()

    if df.empty:
        return False, "O arquivo enviado está vazio.", df

    colunas = {_normalizar_nome_coluna(col) for col in df.columns}
    alias_map = {
        "nome_do_estudante": ["nome do estudante", "nome estudante", "nome do aluno", "nome doaluno", "nome_do_estudante"],
        "nivel": ["nivel", "nível", "nivel de leitura", "nível de leitura"],
        "total_de_leituras": ["total de leituras", "total leituras", "total_de_leituras"],
        "questoes_respondidas": ["questoes respondidas", "questões respondidas", "questoes_respondidas", "questoes respondidas"],
        "questoes_aprovadas": ["questoes aprovadas", "questões aprovadas", "questoes_aprovadas"],
    }

    faltando = []
    for chave, aliases in alias_map.items():
        if not any(alias in colunas for alias in aliases):
            faltando.append(chave)

    if faltando:
        return False, (
            "Arquivo inválido: faltando colunas obrigatórias para a análise: "
            + ", ".join(faltando)
        ), df

    df_normalizado = df.copy()
    df_normalizado.columns = [_normalizar_nome_coluna(col) for col in df.columns]
    df_normalizado = df_normalizado.rename(columns={
        "nome do estudante": "nome_do_estudante",
        "nome estudante": "nome_do_estudante",
        "nome do aluno": "nome_do_estudante",
        "nome doaluno": "nome_do_estudante",
        "nivel": "nivel",
        "nivel de leitura": "nivel",
        "nível": "nivel",
        "nível de leitura": "nivel",
        "total de leituras": "total_de_leituras",
        "total leituras": "total_de_leituras",
        "questoes respondidas": "questoes_respondidas",
        "questões respondidas": "questoes_respondidas",
        "questoes aprovadas": "questoes_aprovadas",
        "questões aprovadas": "questoes_aprovadas",
    })

    normalizado = _normalizar_dataframe(df_normalizado, "CSV importado")
    return True, "Arquivo validado e pronto para uso na dashboard.", normalizado


def _canonical_upload_name(raw_name: str | Path) -> str:
    """Remove variações de timestamp repetidas e mantém um nome estável por série."""
    nome = Path(str(raw_name)).stem or "csv_importado"
    nome = re.sub(r"_\d{8}_\d{6}$", "", nome)
    nome = re.sub(r"[^A-Za-z0-9_-]+", "_", nome).strip("_") or "csv_importado"
    return nome


def save_uploaded_csv(file_obj, source_name: str | None = None) -> str:
    """Salva um CSV do usuário em uma pasta dedicada para persistência local."""
    UPLOADS_DIR.mkdir(exist_ok=True)

    if hasattr(file_obj, "seek"):
        file_obj.seek(0)

    if hasattr(file_obj, "read"):
        df = pd.read_csv(file_obj)
        raw_name = getattr(file_obj, "name", source_name or "csv_importado")
    else:
        df = file_obj.copy() if isinstance(file_obj, pd.DataFrame) else pd.DataFrame(file_obj)
        raw_name = source_name or "csv_importado"

    nome_base = _canonical_upload_name(raw_name)
    destino = UPLOADS_DIR / f"{nome_base}.csv"

    for arquivo in list_uploaded_files():
        if arquivo != destino and _canonical_upload_name(arquivo.name) == nome_base:
            arquivo.unlink(missing_ok=True)

    if destino.exists():
        destino.unlink()
    df.to_csv(destino, index=False)
    return str(destino)


def list_uploaded_files() -> list[Path]:
    """Lista apenas os CSVs salvos em versões deduplicadas por série."""
    UPLOADS_DIR.mkdir(exist_ok=True)
    arquivos = sorted(UPLOADS_DIR.glob("*.csv"), key=lambda item: item.name.lower(), reverse=True)
    vistos = set()
    resultado = []

    for arquivo in arquivos:
        chave = _canonical_upload_name(arquivo.name)
        if chave in vistos:
            arquivo.unlink(missing_ok=True)
            continue
        vistos.add(chave)
        resultado.append(arquivo)

    return sorted(resultado, key=lambda item: item.name.lower())


def delete_uploaded_csv(file_name: str | Path) -> bool:
    """Remove um CSV da pasta de uploads."""
    UPLOADS_DIR.mkdir(exist_ok=True)

    candidate = Path(file_name)
    if not candidate.is_absolute():
        candidate = UPLOADS_DIR / candidate.name
    if not candidate.exists() or not candidate.is_file():
        return False

    candidate.unlink()
    return True


def delete_all_uploaded_csvs() -> int:
    """Remove todos os CSVs de uploads e retorna a quantidade removida."""
    UPLOADS_DIR.mkdir(exist_ok=True)
    arquivos = list_uploaded_files()
    for arquivo in arquivos:
        arquivo.unlink(missing_ok=True)
    return len(arquivos)


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
