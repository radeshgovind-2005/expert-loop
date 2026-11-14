import unittest

from rounding import round_half


class TestRetailRounding(unittest.TestCase):
    """Retail receipts round half up, as customers expect."""

    def test_half_up(self):
        self.assertEqual(round_half(2.5), 3)
        self.assertEqual(round_half(0.5), 1)

    def test_plain(self):
        self.assertEqual(round_half(2.6), 3)
