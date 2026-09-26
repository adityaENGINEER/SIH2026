import os
import sys
import subprocess
from app.core.config import settings

def restore_database(backup_file: str):
    print("Starting Sovereign Data Recovery...")
    
    if settings.persistence_backend != "postgres":
        print("Error: Persistence backend is not set to 'postgres'. Cannot restore to JSON.")
        return

    if not os.path.exists(backup_file):
        print(f"Error: Backup file {backup_file} not found.")
        return

    # We use pg_restore provided by the PostgreSQL client tools
    db_user = os.getenv("POSTGRES_USER", "postgres")
    db_host = os.getenv("POSTGRES_HOST", "localhost")
    db_port = os.getenv("POSTGRES_PORT", "5432")
    db_name = os.getenv("POSTGRES_DB", "sovereignai")
    
    command = [
        "pg_restore",
        "-U", db_user,
        "-h", db_host,
        "-p", db_port,
        "-d", db_name,
        "--clean", # Clean database objects before recreating
        "--if-exists",
        "-1", # Execute as a single transaction
        backup_file
    ]
    
    env = os.environ.copy()
    env["PGPASSWORD"] = os.getenv("POSTGRES_PASSWORD", "postgres_password_here")
    
    try:
        print(f"Restoring database from {backup_file} ...")
        subprocess.run(command, env=env, check=True)
        print("Recovery completed successfully! 🛡️")
    except FileNotFoundError:
        print("Error: 'pg_restore' command not found. Please ensure PostgreSQL client tools are installed on your system.")
    except subprocess.CalledProcessError as e:
        print(f"Error during recovery: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python restore.py <path_to_backup_file.sql>")
    else:
        restore_database(sys.argv[1])
