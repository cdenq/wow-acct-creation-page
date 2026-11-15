"""Send one console command over SOAP and print the raw response, for capturing response strings.

Usage: uv run python scripts/probe.py "server status"
Credentials come from .env, never from the command line.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tofu_signup.config import load_config
from tofu_signup.soap import classify, execute


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit('Usage: uv run python scripts/probe.py "<command>"')
    cfg = load_config()
    resp = execute(cfg.soap_url, cfg.soap_user, cfg.soap_pass, sys.argv[1])
    print(f"HTTP {resp.status}  fault={resp.is_fault}  classified={classify(resp).value}")
    print("--- text ---")
    print(resp.text)
    print("--- raw ---")
    print(resp.raw)


if __name__ == "__main__":
    main()
