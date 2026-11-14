import unittest

from ledger import total


class TestLedger(unittest.TestCase):
    def test_simple(self):
        self.assertEqual(total("date,amount\n2024-01-01,10.00\n2024-01-02,5.50\n"), 15.5)


if __name__ == "__main__":
    unittest.main()
