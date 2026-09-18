# secret-scan-demo

**Deliberate fake-secrets repository for testing secret scanning tools (e.g. Snyk Code).**

This project simulates a small Node.js + Python application with realistic code patterns and variable names, but every credential is **syntactically valid-looking yet entirely fake**. None of these values correspond to real accounts, tokens, or keys, and nothing here can authenticate against a live service.

## Purpose

Use this repo to demonstrate how secret scanners detect hardcoded credentials in:

- Environment files (`.env`)
- JSON configuration
- Application source code
- Infrastructure definitions
- Committed private key files

## What's inside

| Location | Fake secrets embedded |
|----------|----------------------|
| `.env` | AWS keys, `DATABASE_URL`, Stripe secret, JWT secret |
| `config/config.json` | GitHub PAT, Slack bot token |
| `src/routes/webhook.js` | Slack webhook URL, SendGrid API key |
| `scripts/upload.py` | AWS key pair, GCP service account JSON |
| `infra/docker-compose.yml` | Postgres password, Redis auth URL |
| `infra/keys/id_rsa` | SSH private key (committed on purpose) |

## Running locally (optional)

```bash
npm install
npm start
```

```bash
pip install -r requirements.txt
python scripts/upload.py README.md
```

AWS/GCP/Stripe calls will fail — that is expected.

## Important warnings

- **Do not replace fake values with real credentials.**
- **`infra/keys/id_rsa` is committed intentionally** to trigger private-key detection; in a real project this file would belong in `.gitignore`.
- **Do not deploy this application** or point it at production infrastructure.

## Scanner demo tip

Run your secret scanner against this repository root. Findings should map to the locations listed above and illustrate common leakage patterns in small apps.
