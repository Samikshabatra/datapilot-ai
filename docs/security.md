# Security Policy

The latest version of DataPilot AI receives security updates on a best-effort basis.

## Reporting a Vulnerability

If you discover a security issue, please open an issue or contact the maintainer with:

* Description of the vulnerability
* Steps to reproduce
* Potential impact

Please do not publicly disclose vulnerabilities until they have been reviewed.

## Security Notes

* API keys and secrets should never be committed to the repository.
* Environment variables are managed using `.env` files excluded from version control.
* Generated code executes in an isolated environment whenever possible.
