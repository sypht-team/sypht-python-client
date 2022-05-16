import unittest

from sypht.client import SyphtClient


class CreateFileTests(unittest.TestCase):
    def setUp(self):
        self.sypht_client = SyphtClient()

    def test_create_file(self):
        with open("tests/sample_invoice.pdf", "rb") as f:

            response = self.sypht_client.create_file(file=("sample_invoice.pdf", f))
            self.assertTrue(response["status"], "RECIEVED")

    def test_create_file_with_data(self):
        with open("tests/sample_invoice.pdf", "rb") as f:

            response = self.sypht_client.create_file(
                file=("sample_invoice.pdf", f), data={"splitState": "created_by_split"}
            )
            self.assertTrue(response["status"], "RECIEVED")


if __name__ == "__main__":
    unittest.main()
