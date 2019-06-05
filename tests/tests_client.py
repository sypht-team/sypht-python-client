import os
import unittest
import json
import six

import warnings

from sypht.client import SyphtClient, Fieldset

from uuid import UUID


def validate_uuid4(uuid_string):
    try:
        val = UUID(uuid_string, version=4)
    except ValueError:
        return False

    return val.hex == uuid_string.replace('-', '')


class DataExtraction(unittest.TestCase):
    def setUp(self):
        if not six.PY2:
            warnings.simplefilter('ignore', category=ResourceWarning)

        self.sypht_client = SyphtClient(os.environ['CLIENT_ID'], os.environ['CLIENT_SECRET'])

    def test_with_wrong_fieldset(self):
        with self.assertRaises(Exception) as context:
            with open('tests/sample_invoice.pdf', 'rb') as f:
                response = self.sypht_client.upload(f, fieldsets=['sypht.incorrect', ])
                self.assertIn('does not have permission to use fieldSet sypht.incorrect', reponse['error'])

        self.assertTrue('Request failed with status code' in str(context.exception))

    def test_data_extraction_1(self):
        with open('tests/sample_invoice.pdf', 'rb') as f:
            fid = self.sypht_client.upload(f, fieldsets=Fieldset.INVOICE)
            self.assertTrue(validate_uuid4(fid))

        results = self.sypht_client.fetch_results(fid)

        self.assertTrue(isinstance(results, dict))
        self.assertIn('invoice.dueDate', results)
        self.assertIn('invoice.total', results)
        self.assertIn('invoice.amountPaid', results)
        self.assertIn('invoice.amountDue', results)

    def test_data_extraction_2(self):
        with open('tests/sample_invoice.pdf', 'rb') as f:
            fid = self.sypht_client.upload(f, fieldsets=[ Fieldset.INVOICE, Fieldset.BANK, ])
            self.assertTrue(validate_uuid4(fid))

        results = self.sypht_client.fetch_results(fid)

        self.assertTrue(isinstance(results, dict))
        self.assertIn('invoice.dueDate', results)
        self.assertIn('invoice.total', results)
        self.assertIn('invoice.amountPaid', results)
        self.assertIn('invoice.amountDue', results)
        self.assertIn('bank.accountNo', results)
        self.assertIn('bank.bsb', results)


if __name__ == '__main__':
    unittest.main()
