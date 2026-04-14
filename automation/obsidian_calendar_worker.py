from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from automation.obsidian_memory_ai import ObsidianMemoryAIService, _load_dotenv, _resolve_vault_path


def main() -> None:
    _load_dotenv(ROOT / ".env")

    parser = argparse.ArgumentParser(description="Sincroniza pesquisas a partir do calendario para o Obsidian")
    parser.add_argument("--vault", default=os.environ.get("OBSIDIAN_AI_VAULT", "obsidian-ai-vault"))
    parser.add_argument("--provider", default=os.environ.get("OBSIDIAN_AI_PROVIDER", ""))
    parser.add_argument("--model", default=os.environ.get("OBSIDIAN_AI_MODEL", ""))
    parser.add_argument("--temperature", type=float, default=float(os.environ.get("OBSIDIAN_AI_TEMPERATURE", "0.4")))
    args = parser.parse_args()

    service = ObsidianMemoryAIService(
        vault_path=_resolve_vault_path(args.vault),
        provider_alias=args.provider,
        model=args.model,
        temperature=args.temperature,
    )
    result = service.sync_calendar()
    print(result)


if __name__ == "__main__":
    main()
