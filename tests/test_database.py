import unittest

from database import ensure_database, get_turma_data, list_turmas


class DatabaseIntegrationTest(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
