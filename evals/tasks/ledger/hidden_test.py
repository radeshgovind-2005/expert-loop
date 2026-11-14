"""Hidden check for the ledger task. Usage: python3 -I hidden_test.py <workdir>"""
import sys
from decimal import Decimal

sys.path.insert(0, sys.argv[1])
from ledger import total  # noqa: E402

CASES = [
    ("date,amount\n2024-01-01,10.00\n2024-01-02,5.50\n", Decimal("15.50")),
    ('date,memo,amount\n2024-01-01,"rent, jan","1,234.50"\n2024-01-02,x,(34.50)\n', Decimal("1200.00")),
    ("Amount ,date\n$3.10,2024-01-01\n$0.20,2024-01-02\n", Decimal("3.30")),
    ("date,AMOUNT\n2024-01-01,\n2024-01-02,7\n", Decimal("7.00")),
    ('id,amount\n1,"($1,000.00)"\n', Decimal("-1000.00")),
    ("date,amount\n", Decimal("0.00")),
    ("date,amount\n2024-01-01,0.1\n2024-01-01,0.2\n", Decimal("0.30")),
]
fails = 0
for csv_text, want in CASES:
    try:
        got = total(csv_text)
        ok = isinstance(got, Decimal) and got == want and got.as_tuple().exponent == -2
    except Exception as e:  # noqa: BLE001
        got, ok = repr(e), False
    if not ok:
        fails += 1
        print(f"total({csv_text!r}) = {got!r}, want {want!r}")
sys.exit(1 if fails else 0)
