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

        self.assertEqual(results['invoice.dueDate'], '2019-06-05')
        self.assertEqual(results['invoice.total'], '109.88')
        self.assertEqual(results['invoice.amountPaid'], None)
        self.assertEqual(results['invoice.amountDue'], '109.88')

    def test_data_extraction_2(self):
        with open('tests/sample_invoice.pdf', 'rb') as f:
            fid = self.sypht_client.upload(f, fieldsets=[ Fieldset.INVOICE, Fieldset.BANK, ])
            self.assertTrue(validate_uuid4(fid))

        results = self.sypht_client.fetch_results(fid)

        self.assertEqual(results['invoice.dueDate'], '2019-06-05')
        self.assertEqual(results['invoice.total'], '109.88')
        self.assertEqual(results['invoice.amountPaid'], None)
        self.assertEqual(results['invoice.amountDue'], '109.88')
        self.assertEqual(results['bank.accountNo'], '19550021')
        self.assertEqual(results['bank.bsb'], '620119')


if __name__ == '__main__':
    unittest.main()
