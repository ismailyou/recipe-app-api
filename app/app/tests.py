"""
    Sample Test
"""

from django.test import SimpleTestCase
from .calc import calc

class CalcTests(SimpleTestCase):
    """Test the calc module"""

    def test_add_numbers(self):
        """ test adding two numbers"""
        res = calc(5, 6)

        self.assertEqual(res, 12)