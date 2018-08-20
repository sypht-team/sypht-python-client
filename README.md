## Sypht

### Getting started

```
pip install sypht
```


### Example usage

```python
from sypht.client import SyphtClient, Fieldsets

sc = SyphtClient('<client_id>', '<client_secret>')

with open('/Users/andy/Downloads/sample.png', 'rb') as f:
    fid = sc.upload(f, Fieldsets.INVOICE_BPAY_PAYMENT)

print(sc.fetch_results(fid))
```