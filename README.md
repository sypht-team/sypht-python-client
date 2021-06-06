[![PyPI version](https://badge.fury.io/py/sypht.svg)](https://badge.fury.io/py/sypht) [![Build Status](https://api.travis-ci.org/sypht-team/sypht-python-client.svg?branch=master)](https://travis-ci.org/sypht-team/sypht-python-client) [![codecov](https://codecov.io/gh/sypht-team/sypht-python-client/branch/master/graph/badge.svg)](https://codecov.io/gh/sypht-team/sypht-python-client)

# Sypht Python Client

This repository is a Python 3+ reference client implementation for the Sypht API at https://api.sypht.com.

## About Sypht

[Sypht](https://sypht.com) is a SaaS [API](<(https://docs.sypht.com/)>) which extracts key fields from documents and images.

For example, you can upload an image or pdf of a bill or invoice and extract the amount due, due date, invoice number and biller information.

For an up-to-date list of supported extraction types, see the [Marketplace](https://app.sypht.com/marketplace).

## Getting started

To get started you'll need API credentials, i.e. a `<client_id>` and `<client_secret>`, which can be obtained by registering for an [account](https://www.sypht.com/)

## Installation

Latest version is available via pypi:

```
pip install sypht
```

## Usage

```python
from sypht.client import SyphtClient

sc = SyphtClient('<client_id>', '<client_secret>')

with open('invoice.png', 'rb') as f:
    fid = sc.upload(f, products=["forms-&-reports"])

print(sc.fetch_results(fid))
```

or run it via the command line:

```
export SYPHT_API_KEY="<client_id>:<client_secret>"
sypht extract --product invoices path/to/your/document.pdf
```

## Documentation

Visit the [Marketplace](https://app.sypht.com/marketplace/products) to see the full set of available AI Products, document types and data fields supported.

Advanced workflows, features and field data structures are covered in the [Dev Guide](https://sypht.gitbook.io/sypht/).

## License

The software in this repository is available as open source under the terms of the [MIT License](https://github.com/sypht-team/sypht-python-client/blob/master/LICENSE).

## Code of Conduct

Everyone interacting in the project’s codebases, issue trackers, chat rooms and mailing lists is expected to follow the [code of conduct](https://github.com/sypht-team/sypht-python-client/blob/master/CODE_OF_CONDUCT.md).
