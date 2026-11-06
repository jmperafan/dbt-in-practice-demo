#!/usr/bin/env python3
"""PreToolUse hook: block a new model file that doesn't match its layer's
naming convention (AGENTS.md's own rule, enforced rather than advised).

Only checks genuinely new files (Write creating a path that doesn't exist
yet) — an Edit to an existing, already-correctly-named file is never
blocked by this, on purpose: renaming an existing model is a deliberate
refactor, not a naming-convention violation this hook should second-guess.
"""

import json
import os
import re
import sys

LAYER_PREFIXES = {
    "models/staging": r"^stg_[a-z0-9_]+\.sql$",
    "models/intermediate": r"^int_[a-z0-9_]+\.sql$",
    "models/marts": r"^(dim|fct)_[a-z0-9_]+\.sql$",
    "models/context": r"^int_[a-z0-9_]+\.sql$",
}


def main():
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    if payload.get("tool_name") != "Write":
        return 0

    file_path = payload.get("tool_input", {}).get("file_path", "")
    if os.path.exists(file_path):
        return 0

    normalized = file_path.replace(os.sep, "/")
    if not normalized.endswith(".sql"):
        return 0  # properties YAML, doc blocks, etc. — not a model file

    for layer, pattern in LAYER_PREFIXES.items():
        # file_path is always absolute, so match the layer as a path
        # segment anywhere, not just as a literal prefix.
        if normalized.startswith(layer + "/") or ("/" + layer + "/") in normalized:
            filename = os.path.basename(normalized)
            if not re.match(pattern, filename):
                print(
                    f"Blocked: {file_path} doesn't match {layer}'s naming "
                    f"convention ({pattern}). See AGENTS.md.",
                    file=sys.stderr,
                )
                return 2
            return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
