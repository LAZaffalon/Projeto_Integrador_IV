import io
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from database import _discover_dataset_files, delete_uploaded_csv, ensure_database, get_turma_data, list_turmas, list_uploaded_files, save_uploaded_csv


class DatabaseIntegrationTest(unittest.TestCase):
    def test_csv_is_preferred_over_xlsx_for_the_same_series(self):
        with TemporaryDirectory() as temp_dir:
            dataset_dir = Path(temp_dir) / "dataset_clear"
            uploads_dir = Path(temp_dir) / "uploads"
            dataset_dir.mkdir()
            uploads_dir.mkdir()
            (dataset_dir / "turma_2ano.csv").touch()
            (dataset_dir / "turma_2ano.xlsx").touch()
            (dataset_dir / "turma_5ano.xlsx").touch()

            with patch("database.DATASET_DIR", dataset_dir), patch("database.UPLOADS_DIR", uploads_dir):
                arquivos = _discover_dataset_files()

        nomes = {arquivo.name for arquivo in arquivos}
        self.assertIn("turma_2ano.csv", nomes)
        self.assertNotIn("turma_2ano.xlsx", nomes)
        self.assertIn("turma_5ano.xlsx", nomes)

    def test_database_and_data_loading(self):
        ensure_database()
        dados = get_turma_data("2º Ano")
        self.assertFalse(dados.empty)
        self.assertIn("nome_do_estudante", dados.columns)

    def test_3ano_file_is_loaded(self):
        ensure_database()
        turmas = list_turmas()
        self.assertIn("3º Ano", turmas)
        dados = get_turma_data("3º Ano")
        self.assertFalse(dados.empty)
        self.assertIn("nome_do_estudante", dados.columns)

    def test_student_names_are_anonymized(self):
        ensure_database()
        dados = get_turma_data("3º Ano")
        self.assertFalse(dados.empty)
        self.assertTrue(all(str(nome).startswith("Aluno_") for nome in dados["nome_do_estudante"]))
        self.assertNotIn("GUILHAN", " ".join(str(nome) for nome in dados["nome_do_estudante"].head()))

    def test_all_series_are_loaded_and_numeric_fields_are_valid(self):
        ensure_database()
        turmas = list_turmas()
        self.assertGreater(len(turmas), 0)
        self.assertIn("2º Ano", turmas)
        self.assertIn("3º Ano", turmas)
        self.assertIn("5º Ano", turmas)
        self.assertIn("7º Ano", turmas)

        for turma in turmas:
            dados = get_turma_data(turma)
            self.assertFalse(dados.empty)
            self.assertIn("engajamento_leitura", dados.columns)
            self.assertIn("compreensao_textual", dados.columns)
            self.assertIn("total_de_leituras", dados.columns)
            self.assertTrue((dados["engajamento_leitura"] >= 0).all())
            self.assertTrue((dados["compreensao_textual"] >= 0).all())

    def test_uploaded_7ano_file_is_loaded(self):
        ensure_database()
        turmas = list_turmas()
        self.assertIn("7º Ano", turmas)
        dados = get_turma_data("7º Ano")
        self.assertFalse(dados.empty)
        self.assertIn("nome_do_estudante", dados.columns)

    def test_missing_series_returns_empty_dataframe(self):
        ensure_database()
        dados = get_turma_data("Turma Inexistente")
        self.assertTrue(dados.empty)

    def test_upload_validation_accepts_expected_columns(self):
        from database import validate_uploaded_csv

        df = {
            "nome do estudante": ["Aluno_01", "Aluno_02"],
            "total de leituras": [10, 12],
            "questões respondidas": [8, 10],
            "questões aprovadas": [7, 9],
            "nível": ["A", "B"],
            "tempo de leitura": [30, 45],
        }

        valid, message, data = validate_uploaded_csv(df)
        self.assertTrue(valid)
        self.assertIn("nome_do_estudante", data.columns)
        self.assertIn("engajamento_leitura", data.columns)
        self.assertIn("compreensao_textual", data.columns)

    def test_upload_validation_rejects_missing_columns(self):
        from database import validate_uploaded_csv

        df = {
            "nome do estudante": ["Aluno_01"],
            "nível": ["A"],
        }

        valid, message, data = validate_uploaded_csv(df)
        self.assertFalse(valid)
        self.assertIn("faltando", message.lower())

    def test_upload_validation_accepts_realistic_school_csv_variants(self):
        from database import validate_uploaded_csv

        df = {
            "Nome do Estudante": ["Aluno_01", "Aluno_02"],
            "Nível": ["A", "B"],
            "Total de Leituras": [12, 9],
            "Questoes Respondidas": [10, 8],
            "Questoes Aprovadas": [8, 6],
        }

        valid, message, data = validate_uploaded_csv(df)
        self.assertTrue(valid)
        self.assertIn("nome_do_estudante", data.columns)
        self.assertIn("nivel", data.columns)
        self.assertIn("questoes_respondidas", data.columns)
        self.assertIn("questoes_aprovadas", data.columns)

    def test_uploaded_csv_can_be_deleted(self):
        with TemporaryDirectory() as temp_dir:
            csv = io.StringIO(
                "Nome do Estudante,Nível,Total de Leituras,Questões Respondidas,Questões Aprovadas\n"
                "Aluno_01,A,10,8,7\n"
                "Aluno_02,B,12,9,8\n"
            )
            with patch("database.UPLOADS_DIR", Path(temp_dir)):
                caminho = save_uploaded_csv(csv, "arquivo_para_excluir.csv")
                self.assertTrue(Path(caminho).exists())
                self.assertIn(Path(caminho).name, [item.name for item in list_uploaded_files()])

                removido = delete_uploaded_csv(Path(caminho).name)
                self.assertTrue(removido)
                self.assertFalse(Path(caminho).exists())

    def test_uploaded_files_are_deduplicated_by_series_name(self):
        with TemporaryDirectory() as temp_dir:
            uploads_dir = Path(temp_dir)
            arquivos_duplicados = [
                uploads_dir / "7_ANO_C_NOITE_ANUAL_-_7C_-_2025_20261006_211827.csv",
                uploads_dir / "7_ANO_C_NOITE_ANUAL_-_7C_-_2025_20261006_211836.csv",
                uploads_dir / "8_ANO_C_TARDE_ANUAL_-_8B_-_2025_20261006_212425.csv",
                uploads_dir / "8_ANO_C_TARDE_ANUAL_-_8B_-_2025_20261006_212431.csv",
            ]

            for caminho in arquivos_duplicados:
                caminho.write_text("nome do estudante,nivel,total de leituras\nAluno_01,A,10\n", encoding="utf-8")

            with patch("database.UPLOADS_DIR", uploads_dir):
                arquivos = list_uploaded_files()

            nomes = [item.name for item in arquivos]
            nomes_canônicos = {Path(nome).stem.rsplit("_202", 1)[0] if "_202" in Path(nome).stem else Path(nome).stem for nome in nomes}

            self.assertEqual(len(nomes_canônicos), 2)
            self.assertTrue(all(nome.startswith("7_ANO") or nome.startswith("8_ANO") for nome in nomes_canônicos))


if __name__ == "__main__":
    unittest.main()
