import unittest

from finance_parser import parse_number_words, parse_transaction


class NumberParserTests(unittest.TestCase):
    def test_thousands(self) -> None:
        self.assertEqual(parse_number_words("dieciocho mil"), 18_000)

    def test_thousands_with_hundreds(self) -> None:
        self.assertEqual(parse_number_words("veintiocho mil quinientos"), 28_500)

    def test_millions(self) -> None:
        self.assertEqual(parse_number_words("dos millones quinientos mil"), 2_500_000)

    def test_numeric_amount(self) -> None:
        self.assertEqual(parse_number_words("pagué 92.500"), 92_500)


class TransactionParserTests(unittest.TestCase):
    def test_expense(self) -> None:
        parsed = parse_transaction("Ayer compré gasolina por noventa mil")
        self.assertEqual(parsed.movement_type, "expense")
        self.assertEqual(parsed.amount, 90_000)
        self.assertEqual(parsed.category, "Transporte")
        self.assertEqual(parsed.date_rule, "yesterday")

    def test_income(self) -> None:
        parsed = parse_transaction("Me pagaron un millón de salario")
        self.assertEqual(parsed.movement_type, "income")
        self.assertEqual(parsed.amount, 1_000_000)
        self.assertEqual(parsed.category, "Salario")


if __name__ == "__main__":
    unittest.main()

