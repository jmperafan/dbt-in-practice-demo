#!/usr/bin/env python3
"""Load data/raw/*.csv into Snowflake's RAW schema.

This is the one-time "ingestion" step every real dbt project assumes
already happened before dbt ever runs — dbt itself never touches
data/raw/, the same way it wouldn't load a real warehouse's raw schema.
Mirrors ztc-core's own scripts/load_to_snowflake.py; this version is
simpler because this project's data is already clean synthetic CSVs, not a
real messy export, so there's no PII to strip.

Requires:
    pip install snowflake-connector-python pandas

Authenticates with an RSA key pair — Snowflake is deprecating password
login for individual users. Generate one if you don't have one yet:

    openssl genrsa 2048 | openssl pkcs8 -topk8 -v2 aes-256-cbc -inform PEM -out rsa_key.p8
    openssl pkey -in rsa_key.p8 -pubout -out rsa_key.pub
    -- then, in Snowflake, as a user who can alter your own user:
    ALTER USER <your_user> SET RSA_PUBLIC_KEY='<contents of rsa_key.pub, without headers>';

Environment variables (set these before running — same names profiles.yml
reads):
    SNOWFLAKE_ACCOUNT                   - e.g. xy12345.us-east-1
    SNOWFLAKE_USER                      - your Snowflake username
    SNOWFLAKE_PRIVATE_KEY               - contents of your PKCS#8 private key (.p8), not a path
    SNOWFLAKE_PRIVATE_KEY_PASSPHRASE    - omit for an unencrypted key
    SNOWFLAKE_ROLE                      - (optional) defaults to TRANSFORMER
    SNOWFLAKE_DATABASE                  - (optional) defaults to TOPSPIN_TENNIS_ACADEMY
    SNOWFLAKE_WAREHOUSE                 - your Snowflake warehouse name

NOT YET VERIFIED against a real account — written from dbt's and
Snowflake's own documented syntax, but this repo doesn't have sandbox
credentials yet. Run it for real once you do, and fix anything that
doesn't match reality; don't trust this docstring over what actually
happens.
"""

import glob
import os

import pandas as pd
import snowflake.connector
from cryptography.hazmat.primitives import serialization
from snowflake.connector.pandas_tools import write_pandas

HERE = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(HERE, "..", "data", "raw")

ACCOUNT = os.environ["SNOWFLAKE_ACCOUNT"]
USER = os.environ["SNOWFLAKE_USER"]
PRIVATE_KEY_PEM = os.environ["SNOWFLAKE_PRIVATE_KEY"]
PRIVATE_KEY_PASSPHRASE = os.environ.get("SNOWFLAKE_PRIVATE_KEY_PASSPHRASE")
ROLE = os.environ.get("SNOWFLAKE_ROLE", "TRANSFORMER")
DATABASE = os.environ.get("SNOWFLAKE_DATABASE", "TOPSPIN_TENNIS_ACADEMY")
WAREHOUSE = os.environ["SNOWFLAKE_WAREHOUSE"]
SCHEMA = "RAW"


def load_private_key() -> bytes:
    """Decrypt the PKCS#8 key and hand the connector raw DER bytes.

    The connector wants DER, not a PEM string, so the passphrase is applied
    here and the decrypted key only ever exists in memory.
    """
    passphrase = PRIVATE_KEY_PASSPHRASE.encode() if PRIVATE_KEY_PASSPHRASE else None
    key = serialization.load_pem_private_key(PRIVATE_KEY_PEM.encode(), password=passphrase)
    return key.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )


def get_connection():
    return snowflake.connector.connect(
        account=ACCOUNT,
        user=USER,
        private_key=load_private_key(),
        role=ROLE,
        warehouse=WAREHOUSE,
    )


def main():
    csv_files = sorted(glob.glob(os.path.join(RAW_DIR, "*.csv")))
    if not csv_files:
        raise SystemExit(
            "No CSVs found in data/raw/. Run scripts/generate_demo_data.py first."
        )

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(f"USE DATABASE {DATABASE}")
            cur.execute(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA}")
            cur.execute(f"USE SCHEMA {SCHEMA}")

        for path in csv_files:
            table_name = os.path.splitext(os.path.basename(path))[0].upper()
            df = pd.read_csv(path)
            df.columns = [c.upper() for c in df.columns]
            success, nchunks, nrows, _ = write_pandas(
                conn,
                df,
                table_name=table_name,
                database=DATABASE,
                schema=SCHEMA,
                auto_create_table=True,
                overwrite=True,
                quote_identifiers=False,
            )
            status = "OK" if success else "FAILED"
            print(f"{DATABASE}.{SCHEMA}.{table_name:<22} {nrows:>5} rows  {status}")
    finally:
        conn.close()

    print(f"\nLoaded into {DATABASE}.{SCHEMA}")


if __name__ == "__main__":
    main()
