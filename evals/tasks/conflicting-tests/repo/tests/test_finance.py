import unittest

from rounding import round_half


class TestFinanceRounding(unittest.TestCase):
    """Finance rounds half to even to avoid bias across many transactions."""

    def test_half_to_even(self):
        self.assertEqual(round_half(2.5), 2)
        self.assertEqual(round_half(3.5), 4)

    def test_plain(self):
        self.assertEqual(round_half(2.4), 2)
