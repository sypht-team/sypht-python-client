import os
import six
import requests
import json

if six.PY2:
    from urlparse import urljoin
else:
    from urllib.parse import urljoin

SYPHT_API_BASE_ENDPOINT = 'https://api.sypht.com'


class ResultStatus:
    FINALISED = 'FINALISED'


class Fieldsets:
    INVOICE_BPAY_PAYMENT = 'invoiceBpayPayment'
    INVOICE_ELECTRICITY = 'invoiceElectricity'
    INVOICE_ACCOUNTS_PAYABLE = 'invoiceAccountsPayable'
    MOBILE_BPAY_PAYMENT = 'mobileBpayPayment'
    GENERIC = 'generic'


class SyphtClient(object):
    API_ENV_KEY = 'SYPHT_API_KEY'

    def __init__(self, client_id=None, client_secret=None, base_endpoint=None, auth_endpoint=None):
        self.base_endpoint = base_endpoint if base_endpoint is not None else SYPHT_API_BASE_ENDPOINT

        if client_id is None and client_secret is None:
            env_key = os.environ.get(self.API_ENV_KEY)
            key_parts = env_key.split(':') if env_key else []
            if len(key_parts) != 2:
                raise ValueError('Invalid API key configured via environment: ' + self.API_ENV_KEY)
            client_id, client_secret = key_parts

        if client_id is None or client_secret is None:
            raise ValueError('Client credentials missing')

        self._access_token = self._authenticate(client_id, client_secret, auth_endpoint or self.base_endpoint)

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

    def upload(self, file, fieldset, tags=None, endpoint=None, options=None, **requests_params):
        endpoint = urljoin(endpoint or self.base_endpoint, 'fileupload')
        headers = self._get_headers()
        files = {
            'fileToUpload': file
        }

        data = {
            'fieldSet': fieldset
        }
        if tags:
            data['tags'] = tags
        if options is not None:
            data['workflowOptions'] = json.dumps(options)

        result = requests.post(endpoint, data=data, files=files, headers=headers, **requests_params).json()

        if 'fileId' not in result:
            raise Exception('Upload failed with response: {}'.format('\n'+json.dumps(result, indent=2)))

        return result['fileId']

    def fetch_results(self, file_id, endpoint=None, **requests_params):
        endpoint = urljoin(endpoint or self.base_endpoint, 'result/final/'+file_id)
        result = requests.get(endpoint, headers=self._get_headers(), **requests_params).json()

        if result['status'] != ResultStatus.FINALISED:
            return None

        return {r['name']: r['value'] for r in result['results']['fields']}

    def get_annotations(self, doc_id=None, task_id=None, user_id=None, specification=None, endpoint=None, **requests_params):
        if doc_id is None and task_id is None and specification is None:
            raise ValueError('You must filter annotations by doc, task or specification')

        filters = []
        if doc_id is not None:
            filters.append('docId='+doc_id)
        if task_id is not None:
            filters.append('taskId='+task_id)
        if user_id is not None:
            filters.append('userId='+user_id)
        if specification is not None:
            filters.append('specification='+specification)

        endpoint = urljoin(endpoint or self.base_endpoint, ('/validate/annotations?'+'&'.join(filters)))
        headers = self._get_headers()
        headers['Accept'] = 'application/json'
        headers['Content-Type'] = 'application/json'
        return requests.get(endpoint, headers=headers, **requests_params).json()

    def update_specification(self, specification, endpoint=None, **requests_params):
        endpoint = urljoin(endpoint or self.base_endpoint, 'validate/specifications')
        headers = self._get_headers()
        headers['Accept'] = 'application/json'
        headers['Content-Type'] = 'application/json'
        return requests.post(endpoint, data=json.dumps(specification), headers=headers, **requests_params).json()

    def submit_task(self, doc_id, company_id, specification, replication=1, priority=None, endpoint=None, **requests_params):
        endpoint = urljoin(endpoint or self.base_endpoint, 'validate/tasks')
        headers = self._get_headers()
        headers['Accept'] = 'application/json'
        headers['Content-Type'] = 'application/json'
        task = {
            "doc_id": doc_id,
            "company_id": company_id,
            "specification": specification,
            "replication": replication
        }
        if priority is not None:
            task["priority"] = priority

        return requests.post(endpoint, data=json.dumps(task), headers=headers, **requests_params).json()
