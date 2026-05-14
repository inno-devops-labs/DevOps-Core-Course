# Lab 18 Bonus Automation

This bonus folder contains small automation helpers for repeatable validation.

## Files

- `publish-local-demo.sh` - starts a local Kubo container, uploads the Lab 18 assets, and prints the resulting CIDs
- `verify-lab18.sh` - checks the same CID through the local gateway and common public gateways

## Example

```bash
./labs/lab18/bonus/publish-local-demo.sh
./labs/lab18/bonus/verify-lab18.sh <site-cid>
```
