import os
import psycopg2
import psycopg2.extras
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

CSV_PATH = Path("pipeline_data/migration_zcta_net.csv")
TABLE = "migration_zcta_net"


def main():
    # dtype=str preserves leading zeros in zip codes (e.g. "01001" not 1001)
    df = pd.read_csv(CSV_PATH, dtype={"zcta_code": str})

    # CSV month column is "YYYY-MM" — append day so Postgres accepts it as DATE
    df["month"] = pd.to_datetime(df["month"] + "-01").dt.date

    db_url = os.getenv("DATABASE_PUBLIC_URL")
    if not db_url:
        raise ValueError("DATABASE_PUBLIC_URL is missing.")

    conn = psycopg2.connect(db_url)
    cur = conn.cursor()

    cur.execute(f"TRUNCATE TABLE {TABLE}")

    cols = ", ".join(df.columns)
    sql = f"INSERT INTO {TABLE} ({cols}) VALUES %s"

    # .tolist() converts numpy types (float64, int64) to Python natives so psycopg2
    # can adapt them. NaN → None so Postgres receives SQL NULL, not float NaN.
    col_lists = [
        [None if (isinstance(v, float) and pd.isna(v)) else v for v in df[col].tolist()]
        for col in df.columns
    ]
    rows = list(zip(*col_lists))

    psycopg2.extras.execute_values(cur, sql, rows, page_size=2000)

    conn.commit()
    cur.close()
    conn.close()

    print(f"Loaded {len(rows)} rows into '{TABLE}'.")


if __name__ == "__main__":
    main()