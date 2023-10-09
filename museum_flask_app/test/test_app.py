import unittest

from museum_flask_app.src.app import main


class MyTestCase(unittest.TestCase):
    def test_data_formatter(self):
        self.assertEqual(True, True)


if __name__ == '__main__':
    unittest.main()
