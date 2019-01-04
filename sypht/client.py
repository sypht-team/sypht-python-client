import os
import six
import requests
import json

if six.PY2:
    from urlparse import urljoin
else:
    from urllib.parse import urljoin

SYPHT_API_BASE_ENDPOINT = 'https://api.sypht.com'
SYPHT_AUTH_ENDPOINT = 'https://login.sypht.com/oauth/token'

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
            if not env_key:
                raise ValueError('Missing API key configuration. Add ' + self.API_ENV_KEY + ' to the environment or ' +
                                 'directly pass client_id and client_secret parameters to the client constructor.')
            elif env_key and len(key_parts) != 2:
                raise ValueError('Invalid ' + self.API_ENV_KEY + ' environment variable configured')
            client_id, client_secret = key_parts

        if client_id is None or client_secret is None:
            raise ValueError('Client credentials missing')

        self._access_token = self._authenticate(client_id, client_secret, audience=self.base_endpoint, endpoint=auth_endpoint)

    @staticmethod
    def _authenticate(client_id, client_secret, audience, endpoint=None):
        endpoint = endpoint or SYPHT_AUTH_ENDPOINT
        result = requests.post(endpoint, data={
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

    def get_annotations(self, doc_id=None, task_id=None, user_id=None, specification=None, from_date=None, to_date=None, endpoint=None, **requests_params):
        filters = []
        if doc_id is not None:
            filters.append('docId='+doc_id)
        if task_id is not None:
            filters.append('taskId='+task_id)
        if user_id is not None:
            filters.append('userId='+user_id)
        if specification is not None:
            filters.append('specification='+specification)
        if from_date is not None:
            filters.append('fromDate='+from_date)
        if to_date is not None:
            filters.append('toDate='+to_date)

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
