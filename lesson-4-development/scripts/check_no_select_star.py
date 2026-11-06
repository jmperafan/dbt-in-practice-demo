#!/usr/bin/env python3
"""PreToolUse hook: block a Write or Edit that introduces `select *`.

Enforced by tooling, not convention (Lesson 4's shift-left framing): the
cost `select *` prevents is reviewer time and a query breaking the moment
an upstream column gets added, whether the diff came from a person or an
agent. Reads the tool call's JSON off stdin, checks the content actually
being written, and exits 2 (block) with a reason on stderr if it finds one
outside a comment.

Wired into .claude/settings.json as a PreToolUse hook on Write|Edit.
"""

import json
import re
import sys

SELECT_STAR = re.compile(r"select\s*\*", re.IGNORECASE)


def strip_sql_comments(text: str) -> str:
    text = re.sub(r"--.*", "", text)
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    return text


def main():
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    tool_input = payload.get("tool_input", {})
    file_path = tool_input.get("file_path", "")
    if not file_path.endswith(".sql"):
        return 0

    content = tool_input.get("content") or tool_input.get("new_string") or ""
    if SELECT_STAR.search(strip_sql_comments(content)):
        print(
            f"Blocked: {file_path} contains `select *`. "
            "Name the columns explicitly, or source() a staging model that "
            "already does, per Lesson 4's dbt_parse/lint gates.",
            file=sys.stderr,
        )
        return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
