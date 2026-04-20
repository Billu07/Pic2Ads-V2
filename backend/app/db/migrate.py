from pathlib import Path

from app.db.client import get_db_connection

MIGRATIONS_DIR = Path(__file__).resolve().parents[2] / "db" / "migrations"


def ensure_migrations_table() -> None:
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                create table if not exists public.schema_migrations (
                  version text primary key,
                  applied_at timestamptz not null default timezone('utc', now())
                )
                """
            )
        conn.commit()


def applied_versions() -> set[str]:
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("select version from public.schema_migrations")
            rows = cur.fetchall()
    return {str(row["version"]) for row in rows}


def run() -> None:
    ensure_migrations_table()
    applied = applied_versions()
    migration_files = sorted(MIGRATIONS_DIR.glob("*.sql"))

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            for migration in migration_files:
                version = migration.name
                if version in applied:
                    continue

                sql = migration.read_text(encoding="utf-8")
                cur.execute(sql)
                cur.execute(
                    "insert into public.schema_migrations (version) values (%s)",
                    (version,),
                )
                print(f"applied: {version}")
        conn.commit()


if __name__ == "__main__":
    run()

