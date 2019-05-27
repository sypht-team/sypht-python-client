import json
import os

import requests
import six
from base64 import b64decode

if six.PY2:
    from urlparse import urljoin
else:
    from urllib.parse import urljoin


SYPHT_API_BASE_ENDPOINT = 'https://api.sypht.com'
SYPHT_AUTH_ENDPOINT = 'https://login.sypht.com/oauth/token'
SYPHT_OAUTH_COMPANY_ID_CLAIM_KEY = 'https://api.sypht.com/companyId'


class ResultStatus:
    FINALISED = 'FINALISED'


class Fieldset:
    GENERIC = 'sypht.generic'
    DOCUMENT = 'sypht.document'
    INVOICE = 'sypht.invoice'
    BILL = 'sypht.bill'
    BANK = 'sypht.bank'


class SyphtClient(object):
    API_ENV_KEY = 'SYPHT_API_KEY'

    def __init__(self, client_id=None, client_secret=None, base_endpoint=None, auth_endpoint=None, session=None):
        """
        :param client_id: Your Sypht-provided OAuth client_id.
        :param client_secret: Your Sypht-provided OAuth client_secret.
        :param base_endpoint: Sypht API endpoint. Default: `https://api.sypht.com`.
        :param auth_endpoint: Sypht authentication endpoint. Default: `https://login.sypht.com/oauth/token`.
        """
        self.requests = session if session is not None else requests.Session()
        self.base_endpoint = base_endpoint or os.environ.get('SYPHT_API_BASE_ENDPOINT', SYPHT_API_BASE_ENDPOINT)

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

        self._company_id = None
        self._access_token = self._authenticate(client_id, client_secret, audience=self.base_endpoint, endpoint=auth_endpoint)

    @staticmethod
    def _authenticate(client_id, client_secret, audience, endpoint=None):
        endpoint = endpoint or os.environ.get('SYPHT_AUTH_ENDPOINT', SYPHT_AUTH_ENDPOINT)
        result = requests.post(endpoint, data={
            'client_id': client_id,
            'client_secret': client_secret,
            'audience': audience,
            'grant_type': 'client_credentials'
        }).json()

        if result.get('error_description'):
            raise Exception('Authentication failed: {}'.format(result['error_description']))

        return result['access_token']

    @staticmethod
    def _parse_response(response):
        if 200 <= response.status_code < 300:
            return response.json()
        else:
            raise Exception("Request failed with status code ({}): {}".format(response.status_code, response.text))

    @staticmethod
    def _parse_oauth_claims(token):
        part = token.split('.')[1]
        part += "=" * ((4 - len(part) % 4) % 4)
        return json.loads(b64decode(part))

    @property
    def company_id(self):
        if self._company_id is None:
            self._company_id = self._parse_oauth_claims(self._access_token)[SYPHT_OAUTH_COMPANY_ID_CLAIM_KEY]

        return self._company_id

    def _get_headers(self, **headers):
        headers.update({
            'Authorization': 'Bearer ' + self._access_token
        })
        return headers

    def upload(self, file, fieldsets, tags=None, endpoint=None, workflow=None, options=None):
        endpoint = urljoin(endpoint or self.base_endpoint, 'fileupload')
        headers = self._get_headers()
        files = {
            'fileToUpload': file
        }

        if isinstance(fieldsets, str):
            fieldsets = [fieldsets, ]
        data = { 'fieldSets': json.dumps(fieldsets) }
        
        if tags:
            data['tags'] = tags
        if workflow is not None:
            data['workflowId'] = workflow
        if options is not None:
            data['workflowOptions'] = json.dumps(options)

        result = self._parse_response(self.requests.post(endpoint, data=data, files=files, headers=headers))

        if 'fileId' not in result:
            raise Exception('Upload failed with response: {}'.format('\n' + json.dumps(result, indent=2)))

        return result['fileId']

    def fetch_results(self, file_id, endpoint=None, verbose=False):
        endpoint = urljoin(endpoint or self.base_endpoint, 'result/final/' + file_id)
        result = self._parse_response(self.requests.get(endpoint, headers=self._get_headers()))

        if result['status'] != ResultStatus.FINALISED:
            return None

        return result['results'] if verbose else {r['name']: r['value'] for r in result['results']['fields']}
    
    def get_annotations(self, doc_id=None, task_id=None, user_id=None, specification=None, from_date=None, to_date=None, endpoint=None):
        filters = []
        if doc_id is not None:
            filters.append('docId=' + doc_id)
        if task_id is not None:
            filters.append('taskId=' + task_id)
        if user_id is not None:
            filters.append('userId=' + user_id)
        if specification is not None:
            filters.append('specification=' + specification)
        if from_date is not None:
            filters.append('fromDate=' + from_date)
        if to_date is not None:
            filters.append('toDate=' + to_date)

        endpoint = urljoin(endpoint or self.base_endpoint, ('/validate/annotations?' + '&'.join(filters)))
        headers = self._get_headers()
        headers['Accept'] = 'application/json'
        headers['Content-Type'] = 'application/json'
        return self._parse_response(self.requests.get(endpoint, headers=headers))

    def set_company_annotations(self, doc_id, annotations, company_id=None, endpoint=None):
        data = {
            'origin': 'external',
            'fields': [{
                'id': field,
                'type': 'simple',
                'data': {
                    'value': value
                }
            } for field, value in annotations.items()]
        }
        company_id = company_id or self.company_id
        path = "/validate/docs/{}/companyannotation/{}/data".format(doc_id, company_id)
        endpoint = urljoin(endpoint or self.base_endpoint, path)
        headers = self._get_headers()
        headers['Accept'] = 'application/json'
        headers['Content-Type'] = 'application/json'
        return self._parse_response(self.requests.put(endpoint, data=json.dumps(data), headers=headers))

    def update_specification(self, specification, endpoint=None):
        endpoint = urljoin(endpoint or self.base_endpoint, 'validate/specifications')
        headers = self._get_headers()
        headers['Accept'] = 'application/json'
        headers['Content-Type'] = 'application/json'
        return self._parse_response(self.requests.post(endpoint, data=json.dumps(specification), headers=headers))

    def submit_task(self, doc_id, specification, company_id=None, replication=1, priority=None, endpoint=None):
        company_id = company_id or self.company_id
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

        return self._parse_response(self.requests.post(endpoint, data=json.dumps(task), headers=headers))
