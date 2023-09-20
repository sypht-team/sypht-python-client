import unittest
import warnings
from datetime import datetime, timedelta
from http.client import HTTPMessage
from unittest.mock import ANY, Mock, call, patch
from uuid import UUID, uuid4

from sypht.client import SyphtClient


def validate_uuid4(uuid_string):
    try:
        val = UUID(uuid_string, version=4)
    except ValueError:
        return False

    return val.hex == uuid_string.replace("-", "")


class DataExtraction(unittest.TestCase):
    def setUp(self):
        warnings.simplefilter("ignore", category=ResourceWarning)
        self.sypht_client = SyphtClient()

    def test_with_wrong_fieldset(self):
        with self.assertRaises(Exception) as context:
            with open("tests/sample_invoice.pdf", "rb") as f:
                response = self.sypht_client.upload(
                    f,
                    [
                        "sypht.incorrect",
                    ],
                )
                self.assertIn(
                    "does not have permission to use fieldSet sypht.incorrect",
                    response["error"],
                )

        self.assertTrue("Request failed with status code" in str(context.exception))

    def test_data_extraction_1(self):
        with open("tests/sample_invoice.pdf", "rb") as f:
            fid = self.sypht_client.upload(f, ["invoices:2"])
            self.assertTrue(validate_uuid4(fid))

        results = self.sypht_client.fetch_results(fid)

        self.assertTrue(isinstance(results, dict))
        self.assertIn("invoice.dueDate", results)
        self.assertIn("invoice.total", results)
        self.assertIn("invoice.amountPaid", results)
        self.assertIn("invoice.amountDue", results)

    def test_data_extraction_2(self):
        with open("tests/sample_invoice.pdf", "rb") as f:
            fid = self.sypht_client.upload(f, products=["sypht.invoice", "sypht.bank"])
            self.assertTrue(validate_uuid4(fid))

        results = self.sypht_client.fetch_results(fid)

        self.assertTrue(isinstance(results, dict))
        self.assertIn("invoice.dueDate", results)
        self.assertIn("invoice.total", results)
        self.assertIn("invoice.amountPaid", results)
        self.assertIn("invoice.amountDue", results)
        self.assertIn("bank.accountNo", results)
        self.assertIn("bank.bsb", results)

    def test_parent_doc_id(self):
        parent_doc_id = uuid4()
        with open("tests/sample_invoice.pdf", "rb") as f:
            fid = self.sypht_client.upload(f, ["invoices"], parent_doc_id=parent_doc_id)
            self.assertTrue(validate_uuid4(fid))


class ReauthenticateTest(unittest.TestCase):
    def setUp(self):
        self.sypht_client = SyphtClient()
        self.init_access_token = str(self.sypht_client._access_token)
        self.assertFalse(self.sypht_client._is_token_expired())

    def test_no_reauthentication(self):
        # Test non-expired token doesn't require reauthentication
        self.sypht_client.get_company()
        self.assertEqual(self.init_access_token, self.sypht_client._access_token)

    def test_reauthentication(self):
        # Set auth expiry to 1 second ago to avoid mocking datetime
        self.sypht_client._auth_expiry = datetime.utcnow() - timedelta(seconds=1)
        self.assertTrue(self.sypht_client._is_token_expired())

        # Get request will auto-reauthenticate.
        self.sypht_client.get_company()
        self.assertFalse(self.sypht_client._is_token_expired())


class RetryTest(unittest.TestCase):
    """Test the global retry logic works as we expect it to."""

    @patch.object(SyphtClient, "_authenticate_v2", return_value=("access_token", 100))
    @patch.object(SyphtClient, "_authenticate_v1", return_value=("access_token2", 100))
    @patch("urllib3.connectionpool.HTTPConnectionPool._get_conn")
    def test_it_should_eventually_fail_for_50x(
        self, getconn_mock: Mock, auth_v1: Mock, auth_v2: Mock
    ):
        """See https://stackoverflow.com/questions/66497627/how-to-test-retry-attempts-in-python-using-the-request-library ."""

        # arrange
        getconn_mock.return_value.getresponse.side_effect = [
            Mock(status=502, msg=HTTPMessage()),
            # Retries start from here...
            # There should be n for where Retry(status=n).
            Mock(status=502, msg=HTTPMessage()),
            Mock(status=503, msg=HTTPMessage()),
            Mock(status=504, msg=HTTPMessage()),
        ]
        sypht_client = SyphtClient()

        # act / assert
        with self.assertRaisesRegex(Exception, "Max retries exceeded") as e:
            sypht_client.get_annotations(
                from_date=datetime(
                    year=2021, month=1, day=1, hour=0, minute=0, second=0
                ).strftime("%Y-%m-%d"),
                to_date=datetime(
                    year=2021, month=1, day=1, hour=0, minute=0, second=0
                ).strftime("%Y-%m-%d"),
            )
        assert getconn_mock.return_value.request.mock_calls == [
            call(
                "GET",
                "/app/annotations?offset=0&fromDate=2021-01-01&toDate=2021-01-01",
                body=None,
                headers=ANY,
            ),
            # Retries start here...
            call(
                "GET",
                "/app/annotations?offset=0&fromDate=2021-01-01&toDate=2021-01-01",
                body=None,
                headers=ANY,
            ),
            call(
                "GET",
                "/app/annotations?offset=0&fromDate=2021-01-01&toDate=2021-01-01",
                body=None,
                headers=ANY,
            ),
            call(
                "GET",
                "/app/annotations?offset=0&fromDate=2021-01-01&toDate=2021-01-01",
                body=None,
                headers=ANY,
            ),
        ]


if __name__ == "__main__":
    unittest.main()
