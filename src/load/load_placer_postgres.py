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
    df = pd.read_csv(CSV_PATH)

    # CSV month column is "YYYY-MM" — append day so Postgres accepts it as DATE
    df["month"] = pd.to_datetime(df["month"] + "-01").dt.date

    # These columns arrive as floats (e.g. 16344.0) but the table expects INTEGER
    int_cols = [
        "permanent_residents_population",
        "total_pop_change",
        "total_migration",
        "seasonal_visitors",
    ]
    for col in int_cols:
        df[col] = df[col].apply(lambda x: int(x) if pd.notna(x) else None)

    # Swap remaining float NaN → None so psycopg2 writes SQL NULL
    df = df.where(df.notna(), other=None)

    db_url = os.getenv("DATABASE_PUBLIC_URL")
    if not db_url:
        raise ValueError("DATABASE_PUBLIC_URL is missing.")

    conn = psycopg2.connect(db_url)
    cur = conn.cursor()

    cur.execute(f"TRUNCATE TABLE {TABLE}")

    cols = ", ".join(df.columns)
    sql = f"INSERT INTO {TABLE} ({cols}) VALUES %s"
    rows = [tuple(row) for row in df.itertuples(index=False)]

    psycopg2.extras.execute_values(cur, sql, rows, page_size=2000)

    conn.commit()
    cur.close()
    conn.close()

    print(f"Loaded {len(df)} rows into '{TABLE}'.")


if __name__ == "__main__":
    main()
