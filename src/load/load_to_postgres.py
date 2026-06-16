import os
import psycopg2
import psycopg2.extras
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

staging_file = Path("data/staging/adzuna_cleaned.csv")
df = pd.read_csv(staging_file)

def main():
    db_url=os.getenv("DATABASE_PUBLIC_URL")
    if not db_url:
        raise ValueError("Database public URL is missing or incorrect.")
    
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    cur.execute("TRUNCATE TABLE adzuna_it_jobs")
    cols = ", ".join(df.columns)
    sql = f"INSERT INTO adzuna_it_jobs ({cols}) VALUES %s"
    rows = [tuple(row) for row in df.itertuples(index=False)]

    psycopg2.extras.execute_values(cur, sql, rows, page_size=500)

    conn.commit()
    cur.close()
    conn.close()

    print(f"Loaded {len(df)} rows into 'adzuna_it_jobs' table.")

if __name__ =="__main__":
    main()
