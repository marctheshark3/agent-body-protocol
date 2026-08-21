---
name: build-scribe
description: Save a sanitized troubleshooting procedure after an explicitly consented Agent Body help session; never capture secrets or raw screen content.
---

# Build Scribe

After a resolved help session, save only the reusable steps the user approves.

## Redaction gate

Before writing, remove:

- passwords, tokens, credentials, cookies, and recovery codes
- email addresses, personal names, private hostnames, IPs, and file contents
- raw screenshots and copied terminal output unless explicitly approved

Describe controls generically (for example, “select **Send reset link**”), not values entered into fields. If safe sanitization is uncertain, do not save the procedure.
