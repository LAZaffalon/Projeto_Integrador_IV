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

    def test_student_names_are_anonymized(self):
        ensure_database()
        dados = get_turma_data("3º Ano")
        self.assertFalse(dados.empty)
        self.assertTrue(all(str(nome).startswith("Aluno_") for nome in dados["nome_do_estudante"]))
        self.assertNotIn("GUILHAN", " ".join(str(nome) for nome in dados["nome_do_estudante"].head()))


if __name__ == "__main__":
    unittest.main()
