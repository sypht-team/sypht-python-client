[![Build Status](https://api.travis-ci.org/sypht-team/sypht-python-client.svg?branch=master)](https://travis-ci.org/sypht-team/sypht-python-client) [![codecov](https://codecov.io/gh/sypht-team/sypht-python-client/branch/master/graph/badge.svg)](https://codecov.io/gh/sypht-team/sypht-python-client)

## Sypht

Sypht is an service which extracts key fields from documents. For example, you can upload an image or pdf of a bill or invoice and extract the amount due, due date, invoice number and biller information.

Pixels in, json out.

Checkout [sypht.com](https://sypht.com) for more details.

### API

Sypht provides a REST api for interaction with the service. Full documentation is available at: [docs.sypht.com](https://docs.sypht.com/).
This repository is an open-source python reference client implementation for working with the API.

### Getting started

To get started you'll need some API credentials, i.e. a `client_id` and `client_secret`.

Sypht is currently in closed-beta, if you'd like to try out the service contact: [support@sypht.com](mailto://support@sypht.com).

### Installation

Latest version is available via pypi:

```
pip install sypht
```

### Usage

```python
from sypht.client import SyphtClient, Fieldset

sc = SyphtClient('<client_id>', '<client_secret>')

with open('invoice.png', 'rb') as f:
    fid = sc.upload(f, Fieldset.INVOICE)

print(sc.fetch_results(fid))
```

or run it in the command line:

```
$ sypht extract --fieldset sypht.document --fieldset sypht.bank path/to/your/document.pdf
```
