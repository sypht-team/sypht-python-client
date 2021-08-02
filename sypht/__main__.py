#!/usr/bin/env python

import argparse
import json
import re
import sys
import textwrap

from sypht.client import SyphtClient


class Extract(object):
    """Extract values from a document."""

    def __init__(self, path, products):
        self.path = path
        self.products = products

    def __call__(self):
        sypht = SyphtClient()

        print("Uploading: ", self.path, "...")
        with open(self.path, "rb") as f:
            doc_id = sypht.upload(f, self.products)

        print("Processing: ", doc_id, "...")
        print(json.dumps(sypht.fetch_results(doc_id), indent=2))

    @classmethod
    def add_arguments(cls, p):
        p.add_argument("path", metavar="PATH")
        p.add_argument(
            "--product",
            metavar="FIELDSET",
            required=True,
            dest="products",
            action="append",
            help="one or more products.",
        )
        p.set_defaults(cls=cls)
        return p


APPS = [Extract]


def main(args=sys.argv[1:]):
    p = argparse.ArgumentParser(description="Sypht client")
    sp = p.add_subparsers()

    for cls in APPS:
        csp = add_subparser(
            sp, cls, name=re.sub("([A-Z])", r"-\1", cls.__name__).lstrip("-").lower()
        )
        cls.add_arguments(csp)

    namespace = vars(p.parse_args(args))
    if "cls" not in namespace:
        p.print_help(sys.stderr)
    else:
        cls = namespace.pop("cls")
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
        help=doc_text.split("\n")[0],
        description=textwrap.dedent(doc_text.rstrip()),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    return csp


if __name__ == "__main__":
    main()
