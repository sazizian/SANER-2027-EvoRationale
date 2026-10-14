"""Generate an *unapproved* atomic S0 proposal without overwriting input files."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
# Direct-script mode should import the adjacent checkout rather than an
# unrelated older installation available in site-packages.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from evorationale.atomic_state import propose_azure_avnm_atomic_state


def main() -> None:
    parser = argparse.ArgumentParser(description='Propose atomic AVNM S0 for human review only')
    parser.add_argument('--source', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    if args.output.resolve() == args.source.resolve():
        parser.error('--output must differ from --source')
    if args.output.exists():
        parser.error('Refusing to overwrite an existing draft')
    source = json.loads(args.source.read_text(encoding='utf-8'))
    result = propose_azure_avnm_atomic_state(source)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True)+'\n', encoding='utf-8')
    print(json.dumps({'status': 'DRAFT_REQUIRES_HUMAN_REVIEW',
                      'approved': False,
                      'original_unchanged': True,
                      'output': str(args.output),
                      'proposed_central_element_ids': result['central_element_ids']}, indent=2))


if __name__ == '__main__':
    main()
