import six
import requests
import json

if six.PY2:
    from urlparse import urljoin
else:
    from urllib.parse import urljoin


class ResultStatus:
    FINALISED = 'FINALISED'


class Fieldsets:
    INVOICE_BPAY_PAYMENT = 'invoiceBpayPayment'
    INVOICE_ELECTRICITY = 'invoiceElectricity'


class SyphtClient(object):
    def __init__(self, client_id, client_secret, base_endpoint='https://api.sypht.com', auth_endpoint=None):
        self.base_endpoint = base_endpoint
        self._access_token = self._authenticate(client_id, client_secret, auth_endpoint or base_endpoint)

    @staticmethod
    def _authenticate(client_id, client_secret, audience):
        result = requests.post('https://syphen.au.auth0.com/oauth/token', data={
            'client_id': client_id,
            'client_secret': client_secret,
            'audience': audience,
            'grant_type': 'client_credentials'
        }).json()

        if result.get('error_description'):
            raise Exception('Authentication failed: {}'.format(result['error_description']))

        return result['access_token']

    def _get_headers(self, **headers):
        headers.update({
            'Authorization': 'Bearer ' + self._access_token
        })
        return headers

    def upload(self, file, fieldset, endpoint=None):
        endpoint = urljoin(endpoint or self.base_endpoint, 'fileupload')
        headers = self._get_headers()
        files = {
            'fileToUpload': file
        }

        result = requests.post(endpoint, data={
            'fieldSet': fieldset
        }, files=files, headers=headers).json()

        if 'fileId' not in result:
            raise Exception('Upload failed with response: {}'.format('\n'+json.dumps(result, indent=2)))

        return result['fileId']

    def fetch_results(self, file_id, endpoint=None):
        endpoint = urljoin(endpoint or self.base_endpoint, 'result/final/'+file_id)
        result = requests.get(endpoint, headers=self._get_headers()).json()

        if result['status'] != ResultStatus.FINALISED:
            return None

        return {r['name']: r['value'] for r in result['results']['fields']}

    def update_specification(self, specification, endpoint=None):
        endpoint = urljoin(endpoint or self.base_endpoint, 'validate/specifications')
        headers = self._get_headers()
        headers['Accept'] = 'application/json'
        headers['Content-Type'] = 'application/json'
        return requests.post(endpoint, data=json.dumps(specification), headers=headers).json()

    def submit_task(self, doc_id, company_id, specification, replication=1, endpoint=None):
        endpoint = urljoin(endpoint or self.base_endpoint, 'validate/tasks')
        headers = self._get_headers()
        headers['Accept'] = 'application/json'
        headers['Content-Type'] = 'application/json'
        return requests.post(endpoint, data=json.dumps({
            "doc_id": doc_id,
            "company_id": company_id,
            "specification": specification,
            "replication": replication
        }), headers=headers).json()
