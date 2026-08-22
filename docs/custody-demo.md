# Custody judge demo

Two hosts. Fixtures only. Not a TPM claim.

```sh
CUSTODY_BODY_HOST=10.0.0.8 CUSTODY_LEFTOVER_HOST=10.0.0.9 \
  python scripts/custody_demo.py --out /tmp/custody-demo
```

Same-host leftover is refused. Receipts land on the body path, not the installer laptop.

After handoff, a signed vendor artifact may apply. Unsigned or frozen offers refuse. Vendor cannot pull camera. Apply cannot reopen leftover.

A peer lamp may offer a nine-event chirp or a sealed artifact over LED or IR. It cannot take camera, mic, or servos. That is not a live IR PHY claim.


