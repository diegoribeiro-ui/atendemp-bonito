import unittest

from extractor import extract_information


class ExtractorTests(unittest.TestCase):
    def test_extracts_procedure_office_deadline_and_law(self):
        text = """
        NOTÍCIA DE FATO nº 01.2026.00012345-0
        Ofício nº 181/2026. Prazo de 15 dias corridos.
        Noticiante: Maria da Silva
        CPF 123.456.789-00. Lei nº 8.069/1990 e arts. 98, 101 do ECA.
        """
        data = extract_information(text)
        self.assertTrue(any("01.2026.00012345-0" in item for item in data.procedimentos))
        self.assertTrue(any("181/2026" in item for item in data.oficios))
        self.assertIn("15 dias corridos", data.prazos)
        self.assertTrue(any("Maria da Silva" in item for item in data.partes))
        self.assertIn("123.456.789-00", data.cpfs)


if __name__ == "__main__":
    unittest.main()

