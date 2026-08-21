# GitHub Actions adapter (v0 boundary)

Cloud runners cannot reach a loopback/LAN mapper. v0 intentionally ships no tunnel and no public webhook.

On a self-hosted runner already inside the same trusted network, invoke:

```bash
agent-body post --event tests_passed --source github-actions --hal http://127.0.0.1:5001
```

Use `tests_failed` on failure. Do not expose port 5051 to the public internet. A signed webhook adapter is future work.
