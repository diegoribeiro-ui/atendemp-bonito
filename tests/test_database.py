import tempfile
import unittest
from pathlib import Path

from database import Database


class DatabaseTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / "test.db")

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def test_password_roundtrip(self):
        self.db.set_password("senha-segura-123")
        self.assertTrue(self.db.verify_password("senha-segura-123"))
        self.assertFalse(self.db.verify_password("incorreta"))

    def test_create_person_and_appointment(self):
        person_id = self.db.save_person({"nome_completo": "Pessoa Teste", "resumo_caso": "Resumo"})
        self.assertEqual(self.db.get_person(person_id)["nome_completo"], "Pessoa Teste")
        appointment_id = self.db.save_appointment({
            "pessoa_id": person_id, "protocolo": self.db.next_protocol(),
            "data_atendimento": "2026-08-23 10:00", "canal": "Presencial",
            "area": "Cidadania", "assunto": "Teste", "relato": "Relato",
            "retorno_em": "2026-08-24", "lembrete_antecedencia": 1,
        })
        self.assertGreater(appointment_id, 0)
        self.assertEqual(len(self.db.list_appointments()), 1)

    def test_backup(self):
        path = self.db.backup(Path(self.tmp.name) / "backup")
        self.assertTrue(path.exists())


if __name__ == "__main__":
    unittest.main()

