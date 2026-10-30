"""Initialize ecommerce_ci database and schema."""
import os, re
from pathlib import Path
import pymysql
from dotenv import load_dotenv

load_dotenv()
user = os.getenv("MYSQL_USER", "root")
pwd = os.getenv("MYSQL_PASSWORD", "")
host = os.getenv("MYSQL_HOST", "localhost")
port = int(os.getenv("MYSQL_PORT", "3306"))

print(f"Connecting to MySQL at {host}:{port} as {user}...")
conn = pymysql.connect(host=host, port=port, user=user, password=pwd)
cur = conn.cursor()

schema_file = Path(__file__).resolve().parents[1] / "sql" / "schema.sql"
body = re.sub(r"--.*", "", schema_file.read_text(encoding="utf-8"))
statements = [s.strip() for s in body.split(";") if s.strip()]

for st in statements:
    print("Executing:", st[:60].replace("\n", " "), "...")
    cur.execute(st)

conn.commit()
cur.execute("SHOW TABLES IN ecommerce_ci;")
tables = [t[0] for t in cur.fetchall()]
print("Tables in ecommerce_ci:", tables)
conn.close()
print("Schema initialization complete!")
