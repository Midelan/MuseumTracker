import unittest

from museum_flask_app.src.app import main


class MyTestCase(unittest.TestCase):
    def test_data_formatter(self):
        self.assertEqual(True, False)  # add assertion here


if __name__ == '__main__':
    unittest.main()
