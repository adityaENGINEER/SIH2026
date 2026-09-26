import os
import subprocess
from datetime import datetime
from app.core.config import settings

def backup_database():
    print("Starting Sovereign Data Backup...")
    
    if settings.persistence_backend != "postgres":
        print("Error: Persistence backend is not set to 'postgres'. Cannot backup JSON using this script.")
        return

    backup_dir = os.path.join(settings.storage_root, "backups")
    os.makedirs(backup_dir, exist_ok=True)
    
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(backup_dir, f"sovereignai_backup_{timestamp}.sql")
    
    # We use pg_dump provided by the PostgreSQL client tools
    # Expected environment variables or default local params
    db_user = os.getenv("POSTGRES_USER", "postgres")
    db_host = os.getenv("POSTGRES_HOST", "localhost")
    db_port = os.getenv("POSTGRES_PORT", "5432")
    db_name = os.getenv("POSTGRES_DB", "sovereignai")
    
    # This requires pg_dump to be installed on the machine running this script.
    # Alternatively, when running inside Docker, one could execute:
    # docker exec <container_name> pg_dump -U postgres sovereignai > backup.sql
    command = [
        "pg_dump",
        "-U", db_user,
        "-h", db_host,
        "-p", db_port,
        "-d", db_name,
        "-F", "c", # Custom format
        "-f", backup_file
    ]
    
    # For local windows we might need to set PGPASSWORD env variable.
    env = os.environ.copy()
    env["PGPASSWORD"] = os.getenv("POSTGRES_PASSWORD", "postgres_password_here")
    
    try:
        print(f"Backing up database to {backup_file} ...")
        subprocess.run(command, env=env, check=True)
        print("Backup completed successfully! 🎉")
    except FileNotFoundError:
        print("Error: 'pg_dump' command not found. Please ensure PostgreSQL client tools are installed on your system or run this inside the Docker container.")
    except subprocess.CalledProcessError as e:
        print(f"Error during backup: {e}")

if __name__ == "__main__":
    backup_database()
