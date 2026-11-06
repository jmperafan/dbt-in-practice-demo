#!/usr/bin/env bash
# Build plain, pre-built lesson folders at this repo's root, one per
# lesson: start/ (the empty starting point, no dbt project yet) and
# lesson-1-setup/ through lesson-7-governance/ (the finished dbt project
# after that lesson). Each is just a folder, not a nested git repo — they
# get committed into this repo like any other tracked files, so there's
# nothing to rebuild before a demo.
#
# Each lesson folder is also pruned down to what that lesson actually
# introduced: scaffold directories dbt creates by convention but that
# stay empty (just a .gitkeep) until a later lesson populates them —
# seeds/, snapshots/, tests/ before Lesson 6, checks/ before Lesson 8,
# and whichever models/ sublayers that lesson hasn't reached yet — are
# removed rather than shipped empty. The folders look incomplete on
# purpose; that's the point, not a bug. See PRUNE_RULES below to adjust
# when something starts actually being used.
#
# docs/ doesn't survive either: each lesson's own doc (docs/0N-*.md)
# becomes that folder's README.md (replacing the original repo-level
# README), and the rest of docs/ — every earlier lesson's doc, carried
# forward by git archive — is dropped, since that content already has
# its own home in that earlier lesson's own folder. Any doc-to-doc or
# AGENTS.md citation of another lesson's doc is rewritten to point at
# that sibling folder's README.md instead.
#
# lesson-8-deployment/ is deliberately NOT rebuilt here: it's this repo's
# one live, actively-developed dbt project (there's no separate copy
# anywhere else). Wiping and re-extracting it from the frozen
# lesson-8-end tag on every run would silently destroy any work done
# there since. If you ever do need to hard-reset it back to that tag:
#   git archive lesson-8-end | tar -x -C lesson-8-deployment
#
# Usage:
#   scripts/build_demo_repos.sh [output_dir]
#
# output_dir defaults to this repo's own root. Re-running is safe and
# idempotent for start/ and lesson-1-setup/ through lesson-7-governance/:
# each is replaced from scratch, so only rerun this after editing one of
# those lessons, to refresh its folder. See README.md for what's in each
# folder.
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
OUT_DIR="${1:-"$REPO_ROOT"}"
OUT_DIR="$(cd "$(dirname "$OUT_DIR")" && pwd)/$(basename "$OUT_DIR")"

LESSON_8="lesson-8-deployment"

# name -> tag
FOLDERS=(
  "start:lesson-1-start"
  "lesson-1-setup:lesson-1-end"
  "lesson-2-ai-infrastructure:lesson-2-end"
  "lesson-3-sources:lesson-3-end"
  "lesson-4-development:lesson-4-end"
  "lesson-5-documentation:lesson-5-end"
  "lesson-6-testing:lesson-6-end"
  "lesson-7-governance:lesson-7-end"
)

# lesson number (0-8) -> folder name / its own doc's filename. Index 0 is
# "start" (docs/00-introduction.md), which has no numeric suffix in its
# own folder name, so it's handled by position, not by parsing "$name".
FOLDER_FOR=(start lesson-1-setup lesson-2-ai-infrastructure lesson-3-sources lesson-4-development lesson-5-documentation lesson-6-testing lesson-7-governance lesson-8-deployment)
DOC_FOR=(00-introduction.md 01-setup.md 02-ai-infrastructure.md 03-sources.md 04-development.md 05-documentation.md 06-testing.md 07-governance.md 08-deployment.md)

# Rewrite every "docs/0K-*.md" citation anywhere under $1 (README.md,
# AGENTS.md, and plenty of dbt_project.yml/macro/model/packages.yml
# comments too — these docs were cited by path all over the taught
# content, not just in the two obvious files) to point at that lesson's
# own README.md instead — ../<folder>/README.md for a different lesson,
# plain README.md for $2's own number (self-citation). Skips .pdf —
# nothing to rewrite in a binary file, and sed on one risks corrupting it.
fix_doc_refs() {
  local target="$1" self="$2" k f
  find "$target" -type f ! -name "*.pdf" | while read -r f; do
    for k in "${!DOC_FOR[@]}"; do
      if [[ "$k" == "$self" ]]; then
        sed -i "s#docs/${DOC_FOR[$k]}#README.md#g" "$f"
      else
        sed -i "s#docs/${DOC_FOR[$k]}#../${FOLDER_FOR[$k]}/README.md#g" "$f"
      fi
    done
  done
}

# Lowest lesson number (1-8) at which each path first has real content —
# empty (just .gitkeep) in every earlier lesson, so pruned there.
PRUNE_RULES=(
  "tests:6"
  "checks:8"
  "models/intermediate:4"
  "models/marts:4"
  "models/metrics:5"
  "models/context:2"
  "models/staging:2"
)
# seeds/ and snapshots/ are never used by any lesson — always pruned.

mkdir -p "$OUT_DIR"

for entry in "${FOLDERS[@]}"; do
  name="${entry%%:*}"
  tag="${entry##*:}"

  if ! git -C "$REPO_ROOT" rev-parse "$tag" >/dev/null 2>&1; then
    echo "error: tag $tag not found in $REPO_ROOT" >&2
    exit 1
  fi

  target="$OUT_DIR/$name"
  echo "building $name (from $tag) -> $target"
  rm -rf "$target"
  mkdir -p "$target"
  git -C "$REPO_ROOT" archive "$tag" | tar -x -C "$target"

  # One LICENSE at the repo root covers every folder here — no need for
  # a copy in each one.
  rm -f "$target/LICENSE"

  if [[ "$name" == "start" ]]; then
    # No dbt project exists yet at this point in the course — the
    # original README describes the whole project (profiles.yml,
    # dbt_project.yml) which doesn't exist here, so it's confusing
    # rather than useful; the root README already covers this folder.
    # .gitignore is dropped too: every rule in it (dbt artifacts,
    # __pycache__, .venv) addresses something that can't actually
    # happen here — generate_demo_data.py and load_raw_data.py only
    # import stdlib/third-party packages, never each other, so Python
    # never caches bytecode for them regardless of how they're run.
    rm -f "$target/README.md" "$target/.gitignore"
    mv "$target/docs/00-introduction.md" "$target/README.md"
    rm -rf "$target/docs"
    fix_doc_refs "$target" 0
    continue
  fi

  n="${name#lesson-}"
  n="${n%%-*}"

  # data/raw/*.csv is only ever read by scripts/load_raw_data.py (a one-time
  # ingestion step into Snowflake) — no model or seed reads it directly, so
  # every folder after "start" repeats the same ~700K for nothing. Keep it,
  # and the two scripts that only operate on it, only where it's actually
  # demoed from — they can't do anything without data/ next to them.
  rm -rf "$target/data"
  rm -f "$target/scripts/generate_demo_data.py" "$target/scripts/load_raw_data.py"
  rmdir "$target/scripts" 2>/dev/null || true

  # This lesson's own doc replaces the original repo-level README; the
  # rest of docs/ (every earlier lesson's doc, carried forward by git
  # archive) is dropped — it already lives in that earlier lesson's own
  # folder. See this script's header for why.
  rm -f "$target/README.md"
  mv "$target/docs/${DOC_FOR[$n]}" "$target/README.md"
  rm -rf "$target/docs"
  fix_doc_refs "$target" "$n"

  # Scaffold dbt creates by convention but that this lesson hasn't
  # populated yet — see PRUNE_RULES above.
  rm -rf "$target/seeds" "$target/snapshots"
  for rule in "${PRUNE_RULES[@]}"; do
    path="${rule%%:*}"
    first_lesson="${rule##*:}"
    if (( n < first_lesson )); then
      rm -rf "$target/$path"
    fi
  done
  if [[ -d "$target/models" ]] && [[ -z "$(find "$target/models" -type f)" ]]; then
    rm -rf "$target/models"
  fi
  # A .gitkeep that now sits alongside real files (because this lesson
  # populated that directory) serves no purpose.
  find "$target" -name ".gitkeep" | while read -r f; do
    dir=$(dirname "$f")
    if [[ -n "$(find "$dir" -type f ! -name '.gitkeep')" ]]; then
      rm -f "$f"
    fi
  done

  # Cheatsheets aren't part of any tag's tree (they were added after
  # lesson-8-end), so git archive never brings them in — copy this
  # lesson's own one back in from scripts/cheatsheets/, the master store
  # of all of them. That store deliberately isn't inside any lesson
  # folder (lesson-8-deployment used to double as it, which meant it
  # shipped every lesson's cheatsheet instead of just its own). Dropped
  # directly into the lesson folder, no subfolder for a single file.
  sheet=$(ls "$REPO_ROOT/scripts/cheatsheets/cheatsheet-0$n-"*.pdf 2>/dev/null || true)
  if [[ -n "$sheet" ]]; then
    cp "$sheet" "$target/"
  fi

  # check_naming_convention.py (lesson-7 on) had a latent bug predating
  # this whole restructuring: tool_input.file_path is always absolute, so
  # its old `startswith(layer + "/")` check never matched anything, in
  # any lesson, ever. Overwrite with the fixed version from
  # lesson-8-deployment/'s own (never-wiped) copy so the hook actually
  # fires.
  if [[ -f "$target/scripts/check_naming_convention.py" ]]; then
    cp "$OUT_DIR/$LESSON_8/scripts/check_naming_convention.py" "$target/scripts/check_naming_convention.py"
  fi
done

echo "skipping $LESSON_8 (the live project — see this script's header)"
echo "done: $OUT_DIR"
