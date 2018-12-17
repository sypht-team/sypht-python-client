#!/usr/bin/env python
import argparse
import re
import sys
import textwrap
import json
from sypht.client import SyphtClient, Fieldsets


class Extract(object):
    """ Extract values from a document. """
    def __init__(self, path, fieldset):
        self.path = path
        self.fieldset = fieldset

    def __call__(self):
        sypht = SyphtClient()

        print('Uploading: ', self.path, '...')
        with open(self.path, 'rb') as f:
            doc_id = sypht.upload(f, self.fieldset)

        print('Processing: ', doc_id, '...')
        print(json.dumps(sypht.fetch_results(doc_id), indent=2))

    @classmethod
    def add_arguments(cls, p):
        p.add_argument('path', metavar='PATH')
        p.add_argument('--fieldset',
                       metavar='FIELDSET',
                       required=False,
                       default=Fieldsets.INVOICE_ACCOUNTS_PAYABLE,
                       choices=[
                           Fieldsets.INVOICE_BPAY_PAYMENT,
                           Fieldsets.INVOICE_ELECTRICITY,
                           Fieldsets.INVOICE_ACCOUNTS_PAYABLE,
                           Fieldsets.MOBILE_BPAY_PAYMENT,
                           Fieldsets.GENERIC
                       ])
        p.set_defaults(cls=cls)
        return p


APPS = [
    Extract
]


def main(args=sys.argv[1:]):
    p = argparse.ArgumentParser(description='Sypht client')
    sp = p.add_subparsers()

    for cls in APPS:
        csp = add_subparser(sp, cls, name=re.sub('([A-Z])', r'-\1', cls.__name__).lstrip('-').lower())
        cls.add_arguments(csp)

    namespace = vars(p.parse_args(args))
    if 'cls' not in namespace:
        p.print_help(sys.stderr)
    else:
        cls = namespace.pop('cls')
        try:
            obj = cls(**namespace)
        except ValueError as e:
            p.error(str(e))
        obj()


def add_subparser(sp, cls, name=None, doc_text=None):
    name = name or cls.__name__
    doc_text = doc_text or cls.__doc__
    csp = sp.add_parser(
        name,
        help=doc_text.split('\n')[0],
        description=textwrap.dedent(doc_text.rstrip()),
        formatter_class=argparse.RawDescriptionHelpFormatter)
    return csp


if __name__ == '__main__':
    main()