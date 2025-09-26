#!/usr/bin/env python3
"""Database migration management script."""

import subprocess
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from app.database import create_tables, drop_tables


def run_alembic_command(command: str) -> int:
    """Run an alembic command and return the exit code."""
    return subprocess.run(
        ["pipenv", "run", "alembic"] + command.split(), cwd=Path(__file__).parent.parent
    ).returncode


def init_db():
    """Initialize the database by creating all tables."""
    print("Creating database tables...")
    create_tables()
    print("Database tables created successfully!")


def drop_db():
    """Drop all database tables."""
    print("Dropping database tables...")
    drop_tables()
    print("Database tables dropped successfully!")


def create_migration(message: str):
    """Create a new migration."""
    print(f"Creating migration: {message}")
    return run_alembic_command(f'revision --autogenerate -m "{message}"')


def upgrade_db(revision: str = "head"):
    """Upgrade database to a specific revision."""
    print(f"Upgrading database to {revision}...")
    return run_alembic_command(f"upgrade {revision}")


def downgrade_db(revision: str = "-1"):
    """Downgrade database to a specific revision."""
    print(f"Downgrading database to {revision}...")
    return run_alembic_command(f"downgrade {revision}")


def show_history():
    """Show migration history."""
    return run_alembic_command("history")


def show_current():
    """Show current migration."""
    return run_alembic_command("current")


def main():
    """Main migration script."""
    if len(sys.argv) < 2:
        print("Usage: python migrate.py <command> [args...]")
        print("Commands:")
        print("  init                    - Create all tables")
        print("  drop                    - Drop all tables")
        print("  create <message>        - Create new migration")
        print("  upgrade [revision]      - Upgrade database")
        print("  downgrade [revision]    - Downgrade database")
        print("  history                 - Show migration history")
        print("  current                 - Show current migration")
        sys.exit(1)

    command = sys.argv[1]

    if command == "init":
        init_db()
    elif command == "drop":
        drop_db()
    elif command == "create":
        if len(sys.argv) < 3:
            print("Error: Migration message required")
            sys.exit(1)
        message = sys.argv[2]
        sys.exit(create_migration(message))
    elif command == "upgrade":
        revision = sys.argv[2] if len(sys.argv) > 2 else "head"
        sys.exit(upgrade_db(revision))
    elif command == "downgrade":
        revision = sys.argv[2] if len(sys.argv) > 2 else "-1"
        sys.exit(downgrade_db(revision))
    elif command == "history":
        sys.exit(show_history())
    elif command == "current":
        sys.exit(show_current())
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
