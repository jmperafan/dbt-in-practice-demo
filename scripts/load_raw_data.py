#!/usr/bin/env python3
"""Load data/raw/*.csv into the `raw` schema of the local DuckDB file dbt reads from.

This is the one-time "ingestion" step every real dbt project assumes already
happened before dbt ever runs. It mirrors ztc-core's scripts/load_to_snowflake.py,
pointed at a local DuckDB file instead of Snowflake, so the same raw.* tables
sources.yml points at (Lesson 3) actually exist before you get there — dbt
itself never loads this data, the same way it wouldn't load a real warehouse's
raw schema.

Stdlib only, shelling out to the `duckdb` CLI rather than the duckdb Python
package, so there's nothing to pip install: the CLI is the one thing this
script needs beyond dbt itself.

Run it once after cloning, and again any time you regenerate the CSVs with
scripts/generate_demo_data.py.
"""

import glob
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(HERE, "..", "data", "raw")
DB_PATH = os.path.join(HERE, "..", "sutton.duckdb")


def main():
    duckdb_cli = shutil.which("duckdb")
    if not duckdb_cli:
        raise SystemExit(
            "duckdb CLI not found on PATH. Install it (https://duckdb.org/docs/installation/) "
            "then re-run this script."
        )

    csv_files = sorted(glob.glob(os.path.join(RAW_DIR, "*.csv")))
    if not csv_files:
        raise SystemExit(
            "No CSVs found in data/raw/. Run scripts/generate_demo_data.py first."
        )

    statements = ["create schema if not exists raw;"]
    for path in csv_files:
        table = os.path.splitext(os.path.basename(path))[0]
        abs_path = os.path.abspath(path).replace("'", "''")
        statements.append(f"drop table if exists raw.{table};")
        statements.append(
            f"create table raw.{table} as "
            f"select * from read_csv_auto('{abs_path}', header=true);"
        )
    statements.append("select table_name, estimated_size from duckdb_tables() "
                       "where schema_name = 'raw' order by table_name;")

    result = subprocess.run(
        [duckdb_cli, DB_PATH],
        input="\n".join(statements),
        text=True,
        capture_output=True,
    )
    print(result.stdout)
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        raise SystemExit(result.returncode)

    print(f"Loaded into {os.path.relpath(DB_PATH)}")


if __name__ == "__main__":
    main()
