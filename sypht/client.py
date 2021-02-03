import json
import os
from base64 import b64encode
from datetime import datetime, timedelta
from urllib.parse import urljoin

import requests

SYPHT_API_BASE_ENDPOINT = "https://api.sypht.com"
SYPHT_AUTH_ENDPOINT = "https://auth.sypht.com/oauth2/token"
SYPHT_LEGACY_AUTH_ENDPOINT = "https://login.sypht.com/oauth/token"
SYPHT_OAUTH_COMPANY_ID_CLAIM_KEY = "https://api.sypht.com/companyId"


def _iter_chunked_sequence(seq, size):
    for pos in range(0, len(seq), size):
        yield seq[pos : pos + size]


class SyphtClient(object):
    API_ENV_KEY = "SYPHT_API_KEY"

    def __init__(
        self,
        client_id=None,
        client_secret=None,
        base_endpoint=None,
        auth_endpoint=None,
        session=None,
    ):
        """
        :param client_id: Your Sypht-provided OAuth client_id.
        :param client_secret: Your Sypht-provided OAuth client_secret.
        :param base_endpoint: Sypht API endpoint. Default: `https://api.sypht.com`.
        :param auth_endpoint: Sypht authentication endpoint. Default: `https://login.sypht.com/oauth/token`.
        """
        self.requests = session if session is not None else requests.Session()
        self.base_endpoint = base_endpoint or os.environ.get(
            "SYPHT_API_BASE_ENDPOINT", SYPHT_API_BASE_ENDPOINT
        )
        self.audience = os.environ.get("SYPHT_AUDIENCE", self.base_endpoint)
        self.auth_endpoint = auth_endpoint or os.environ.get(
            "SYPHT_AUTH_ENDPOINT", SYPHT_AUTH_ENDPOINT
        )

        if client_id is None and client_secret is None:
            env_key = os.environ.get(self.API_ENV_KEY)
            key_parts = env_key.split(":") if env_key else []
            if not env_key:
                raise ValueError(
                    "Missing API key configuration. Add "
                    + self.API_ENV_KEY
                    + " to the environment or "
                    + "directly pass client_id and client_secret parameters to the client constructor."
                )
            elif env_key and len(key_parts) != 2:
                raise ValueError(
                    "Invalid " + self.API_ENV_KEY + " environment variable configured"
                )
            client_id, client_secret = key_parts

        if client_id is None or client_secret is None:
            raise ValueError("Client credentials missing")

        self.client_id = client_id
        self._client_secret = client_secret
        self._company_id = None
        self._authenticate_client()

    @staticmethod
    def _authenticate_v2(endpoint, client_id, client_secret, audience):
        basic_auth_slug = b64encode((client_id + ":" + client_secret).encode("utf-8")).decode(
            "utf-8"
        )
        result = requests.post(
            endpoint,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/x-www-form-urlencoded",
                "Authorization": f"Basic {basic_auth_slug}",
            },
            data=f"client_id={client_id}&grant_type=client_credentials",
            allow_redirects=False,
        ).json()

        if result.get("error"):
            raise Exception("Authentication failed: {}".format(result["error"]))

        return result["access_token"], result["expires_in"]

    @staticmethod
    def _authenticate_v1(endpoint, client_id, client_secret, audience):
        endpoint = endpoint or os.environ.get("SYPHT_AUTH_ENDPOINT", SYPHT_LEGACY_AUTH_ENDPOINT)
        result = requests.post(
            endpoint,
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "audience": audience,
                "grant_type": "client_credentials",
            },
        ).json()

        if result.get("error_description"):
            raise Exception("Authentication failed: {}".format(result["error_description"]))

        return result["access_token"], result["expires_in"]

    @staticmethod
    def _parse_response(response):
        if 200 <= response.status_code < 300:
            return response.json()
        else:
            raise Exception(
                "Request failed with status code ({}): {}".format(
                    response.status_code, response.text
                )
            )

    @property
    def company_id(self):
        if self._company_id is None:
            self._company_id = self.get_company()["id"]

        return self._company_id

    def _is_token_expired(self):
        return datetime.utcnow() > self._auth_expiry

    def _authenticate_client(self):
        if "/oauth/" in self.auth_endpoint:
            access_token, expires_in = self._authenticate_v1(
                self.auth_endpoint, self.client_id, self._client_secret, audience=self.audience
            )
        elif "/oauth2/" in self.auth_endpoint:
            access_token, expires_in = self._authenticate_v2(
                self.auth_endpoint, self.client_id, self._client_secret, audience=self.audience
            )
        else:
            raise ValueError(f"Invalid authentication endpoint: {auth_endpoint}")

        self._auth_expiry = datetime.utcnow() + timedelta(seconds=expires_in)
        self._access_token = access_token

    def _get_headers(self, **headers):
        if self._is_token_expired():
            self._authenticate_client()

        headers.update({"Authorization": "Bearer " + self._access_token})
        return headers

    def get_company(self, endpoint=None):
        return self.get_company_by_client_id(self.client_id, endpoint=endpoint)

    def get_company_by_client_id(self, client_id, endpoint=None):
        endpoint = urljoin(
            endpoint or self.base_endpoint, f"/app/company/byclientid/{client_id}"
        )
        headers = self._get_headers()
        headers["Accept"] = "application/json"
        headers["Content-Type"] = "application/json"
        return self._parse_response(self.requests.get(endpoint, headers=headers))

    def upload(
        self,
        file,
        products,
        tags=None,
        endpoint=None,
        workflow=None,
        options=None,
        headers=None,
        parent_doc_id=None,
    ):
        endpoint = urljoin(endpoint or self.base_endpoint, "fileupload")
        headers = headers or {}
        headers = self._get_headers(**headers)
        files = {"fileToUpload": file}

        if isinstance(products, str):
            products = [
                products,
            ]
        data = {"products": json.dumps(products)}

        if tags:
            data["tags"] = tags
        if workflow is not None:
            data["workflowId"] = workflow
        if options is not None:
            data["workflowOptions"] = json.dumps(options)
        if parent_doc_id is not None:
            data["parentDocId"] = parent_doc_id

        result = self._parse_response(
            self.requests.post(endpoint, data=data, files=files, headers=headers)
        )

        if "fileId" not in result:
            raise Exception(
                "Upload failed with response: {}".format("\n" + json.dumps(result, indent=2))
            )

        return result["fileId"]

    def fetch_results(self, file_id, endpoint=None, verbose=False, headers=None):
        endpoint = urljoin(endpoint or self.base_endpoint, "result/final/" + file_id)
        if verbose:
            endpoint += "?verbose=true"
        headers = headers or {}
        headers = self._get_headers(**headers)
        result = self._parse_response(self.requests.get(endpoint, headers=headers))

        if result["status"] != "FINALISED":
            return None

        return (
            result["results"]
            if verbose
            else {r["name"]: r["value"] for r in result["results"]["fields"]}
        )

    def get_annotations(
        self,
        doc_id=None,
        task_id=None,
        user_id=None,
        specification=None,
        from_date=None,
        to_date=None,
        endpoint=None,
    ):
        filters = []
        if doc_id is not None:
            filters.append("docId=" + doc_id)
        if task_id is not None:
            filters.append("taskId=" + task_id)
        if user_id is not None:
            filters.append("userId=" + user_id)
        if specification is not None:
            filters.append("specification=" + specification)
        if from_date is not None:
            filters.append("fromDate=" + from_date)
        if to_date is not None:
            filters.append("toDate=" + to_date)

        endpoint = urljoin(
            endpoint or self.base_endpoint, ("/app/annotations?" + "&".join(filters))
        )
        headers = self._get_headers()
        headers["Accept"] = "application/json"
        headers["Content-Type"] = "application/json"
        return self._parse_response(self.requests.get(endpoint, headers=headers))

    def get_annotations_for_docs(self, doc_ids, endpoint=None):
        body = json.dumps({"docIds": doc_ids})
        endpoint = urljoin(endpoint or self.base_endpoint, ("/app/annotations/search"))
        headers = self._get_headers()
        headers["Accept"] = "application/json"
        headers["Content-Type"] = "application/json"
        return self._parse_response(self.requests.post(endpoint, data=body, headers=headers))

    def set_company_annotations(self, doc_id, annotations, company_id=None, endpoint=None):
        data = {
            "origin": "external",
            "fields": [
                {"id": field, "type": "simple", "data": {"value": value}}
                for field, value in annotations.items()
            ],
        }
        company_id = company_id or self.company_id
        path = "/app/docs/{}/companyannotation/{}/data".format(doc_id, company_id)
        endpoint = urljoin(endpoint or self.base_endpoint, path)
        headers = self._get_headers()
        headers["Accept"] = "application/json"
        headers["Content-Type"] = "application/json"
        return self._parse_response(
            self.requests.put(endpoint, data=json.dumps(data), headers=headers)
        )

    def get_tag(self, tag, company_id=None, endpoint=None):
        company_id = company_id or self.company_id
        endpoint = urljoin(
            endpoint or self.base_endpoint,
            f"app/company/{company_id}/tags/{tag}",
        )
        headers = self._get_headers()
        headers["Accept"] = "application/json"
        headers["Content-Type"] = "application/json"
        return self._parse_response(self.requests.get(endpoint, headers=headers))

    def create_tag(self, tag, description=None, company_id=None, endpoint=None):
        company_id = company_id or self.company_id
        endpoint = urljoin(
            endpoint or self.base_endpoint,
            f"app/company/{company_id}/tags",
        )
        headers = self._get_headers()
        headers["Accept"] = "application/json"
        headers["Content-Type"] = "application/json"
        return self._parse_response(self.requests.post(endpoint, data=json.dumps({
            "name": tag,
            "description": description
        }), headers=headers))

    def delete_tag(self, tag, company_id=None, endpoint=None):
        company_id = company_id or self.company_id
        endpoint = urljoin(
            endpoint or self.base_endpoint,
            f"app/company/{company_id}/tags/{tag}",
        )
        headers = self._get_headers()
        headers["Accept"] = "application/json"
        headers["Content-Type"] = "application/json"
        return self._parse_response(self.requests.delete(endpoint, headers=headers))

    def get_files_for_tag(self, tag, company_id=None, endpoint=None):
        company_id = company_id or self.company_id
        endpoint = urljoin(
            endpoint or self.base_endpoint,
            f"app/company/{company_id}/tags/{tag}/documents",
        )
        headers = self._get_headers()
        headers["Accept"] = "application/json"
        headers["Content-Type"] = "application/json"
        return self._parse_response(self.requests.get(endpoint, headers=headers))

    def set_files_for_tag(self, tag, file_ids, company_id=None, endpoint=None):
        company_id = company_id or self.company_id
        endpoint = urljoin(
            endpoint or self.base_endpoint,
            f"app/company/{company_id}/tags/{tag}/documents",
        )
        headers = self._get_headers()
        headers["Accept"] = "application/json"
        headers["Content-Type"] = "application/json"
        return self._parse_response(
            self.requests.put(endpoint, data=json.dumps({"docs": file_ids}), headers=headers)
        )

    def add_files_to_tag(self, tag, file_ids, company_id=None, endpoint=None):
        company_id = company_id or self.company_id
        endpoint = urljoin(
            endpoint or self.base_endpoint,
            f"app/company/{company_id}/tags/{tag}/documents",
        )
        headers = self._get_headers()
        headers["Accept"] = "application/json"
        headers["Content-Type"] = "application/json"
        return self._parse_response(
            self.requests.patch(endpoint, data=json.dumps({"docs": file_ids}), headers=headers)
        )

    def remove_file_from_tag(self, file_id, tag, company_id=None, endpoint=None):
        company_id = company_id or self.company_id
        endpoint = urljoin(
            endpoint or self.base_endpoint,
            f"app/company/{company_id}/tags/{tag}/documents/{file_id}",
        )
        headers = self._get_headers()
        headers["Accept"] = "application/json"
        headers["Content-Type"] = "application/json"
        return self._parse_response(self.requests.delete(endpoint, headers=headers))

    def get_tags_for_file(self, file_id, company_id=None, endpoint=None):
        company_id = company_id or self.company_id
        endpoint = urljoin(
            endpoint or self.base_endpoint,
            f"app/company/{company_id}/documents/{file_id}/tags",
        )
        headers = self._get_headers()
        headers["Accept"] = "application/json"
        headers["Content-Type"] = "application/json"
        return self._parse_response(self.requests.get(endpoint, headers=headers))

    def set_tags_for_file(self, file_id, tags, company_id=None, endpoint=None):
        company_id = company_id or self.company_id
        endpoint = urljoin(
            endpoint or self.base_endpoint,
            f"app/company/{company_id}/documents/{file_id}/tags",
        )
        headers = self._get_headers()
        headers["Accept"] = "application/json"
        headers["Content-Type"] = "application/json"
        return self._parse_response(
            self.requests.put(endpoint, data=json.dumps({"tags": tags}), headers=headers)
        )

    def add_tags_to_file(self, file_id, tags, company_id=None, endpoint=None):
        company_id = company_id or self.company_id
        endpoint = urljoin(
            endpoint or self.base_endpoint,
            f"app/company/{company_id}/documents/{file_id}/tags",
        )
        headers = self._get_headers()
        headers["Accept"] = "application/json"
        headers["Content-Type"] = "application/json"
        return self._parse_response(
            self.requests.patch(endpoint, data=json.dumps({"tags": tags}), headers=headers)
        )

    def get_entity(self, entity_id, entity_type, company_id=None, endpoint=None):
        company_id = company_id or self.company_id
        endpoint = urljoin(
            endpoint or self.base_endpoint,
            f"storage/{company_id}/entity/{entity_type}/{entity_id}",
        )
        headers = self._get_headers()
        headers["Accept"] = "application/json"
        headers["Content-Type"] = "application/json"
        return self._parse_response(self.requests.get(endpoint, headers=headers))

    def set_entity(self, entity_id, entity_type, data, company_id=None, endpoint=None):
        company_id = company_id or self.company_id
        endpoint = urljoin(
            endpoint or self.base_endpoint,
            f"storage/{company_id}/entity/{entity_type}/{entity_id}",
        )
        headers = self._get_headers()
        headers["Accept"] = "application/json"
        headers["Content-Type"] = "application/json"
        return self._parse_response(
            self.requests.put(endpoint, data=json.dumps(data), headers=headers)
        )

    def delete_entity(self, entity_id, entity_type, company_id=None, endpoint=None):
        company_id = company_id or self.company_id
        endpoint = urljoin(
            endpoint or self.base_endpoint,
            f"storage/{company_id}/entity/{entity_type}/{entity_id}",
        )
        headers = self._get_headers()
        headers["Accept"] = "application/json"
        headers["Content-Type"] = "application/json"
        return self._parse_response(self.requests.delete(endpoint, headers=headers))

    def set_many_entities(
        self, entity_type, entities, batch_size=1000, company_id=None, endpoint=None
    ):
        """
        Updates a set of entities in bulk.

        Entities should be list with structure:
        [
            {"entity_id": "id_0", "data": {"some_field": "abc123", "Another Field": "2020-11-04"}},
            {"entity_id": "id_1", "data": {"some_field": "abc124", "Another Field": "2020-11-05"}},
            {"entity_id": "id_2", "data": {"some_field": "ghi789", "Another Field": "2020-11-06"}}
            ...
        ]
        """
        if entities is None or not isinstance(entities, list):
            raise ValueError("Expected a list of entities")

        company_id = company_id or self.company_id
        endpoint = urljoin(
            endpoint or self.base_endpoint,
            f"storage/{company_id}/bulkentity/{entity_type}/",
        )
        headers = self._get_headers()
        headers["Accept"] = "application/json"
        headers["Content-Type"] = "application/json"

        responses = []
        for batch in _iter_chunked_sequence(entities, batch_size):
            responses.append(
                self._parse_response(
                    self.requests.post(endpoint, data=json.dumps(batch), headers=headers)
                )
            )
        return responses

    def search_entities(
        self, entity_type, exact=None, fuzzy=None, company_id=None, endpoint=None
    ):
        exact = exact or {}
        fuzzy = fuzzy or {}
        company_id = company_id or self.company_id
        endpoint = urljoin(
            endpoint or self.base_endpoint, f"storage/{company_id}/entitysearch/{entity_type}/"
        )
        headers = self._get_headers()
        headers["Accept"] = "application/json"
        headers["Content-Type"] = "application/json"
        return self._parse_response(
            self.requests.post(
                endpoint,
                data=json.dumps({"exact": exact, "fuzzy": fuzzy}),
                headers=headers,
            )
        )

    def update_specification(self, specification, endpoint=None):
        endpoint = urljoin(endpoint or self.base_endpoint, "app/specifications")
        headers = self._get_headers()
        headers["Accept"] = "application/json"
        headers["Content-Type"] = "application/json"
        return self._parse_response(
            self.requests.post(endpoint, data=json.dumps(specification), headers=headers)
        )

    def submit_task(
        self,
        doc_id,
        specification,
        company_id=None,
        replication=1,
        priority=None,
        endpoint=None,
    ):
        company_id = company_id or self.company_id
        endpoint = urljoin(endpoint or self.base_endpoint, "app/tasks")
        headers = self._get_headers()
        headers["Accept"] = "application/json"
        headers["Content-Type"] = "application/json"
        task = {
            "docId": doc_id,
            "companyId": company_id,
            "specification": specification,
            "replication": replication,
        }
        if priority is not None:
            task["priority"] = priority

        return self._parse_response(
            self.requests.post(endpoint, data=json.dumps(task), headers=headers)
        )
