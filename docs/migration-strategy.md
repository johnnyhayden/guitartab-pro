# Database Migration Strategy

## Overview

This document outlines the database migration strategy for GuitarTab Pro using Alembic and SQLAlchemy.

## Migration Tools

### Alembic Configuration
- **Location**: `backend/alembic/`
- **Config File**: `backend/alembic.ini`
- **Environment**: `backend/alembic/env.py`

### Migration Script
- **Location**: `backend/scripts/migrate.py`
- **Purpose**: Simplified migration management
- **Usage**: `python scripts/migrate.py <command>`

## Migration Commands

### Using the Migration Script

```bash
# Initialize database (create all tables)
python scripts/migrate.py init

# Drop all tables
python scripts/migrate.py drop

# Create new migration
python scripts/migrate.py create "Add user preferences table"

# Upgrade to latest migration
python scripts/migrate.py upgrade

# Downgrade by one migration
python scripts/migrate.py downgrade

# Show migration history
python scripts/migrate.py history

# Show current migration
python scripts/migrate.py current
```

### Using Make Commands

```bash
# Initialize database
make db-init

# Drop all tables
make db-drop

# Create new migration (interactive)
make db-migrate

# Upgrade database
make db-upgrade

# Downgrade database
make db-downgrade
```

### Using Alembic Directly

```bash
# Create new migration
pipenv run alembic revision --autogenerate -m "Description"

# Upgrade database
pipenv run alembic upgrade head

# Downgrade database
pipenv run alembic downgrade -1

# Show current revision
pipenv run alembic current

# Show migration history
pipenv run alembic history
```

## Migration Workflow

### 1. Development Workflow

1. **Make Model Changes**: Update SQLAlchemy models in `src/app/models/`
2. **Create Migration**: Run `make db-migrate` or `python scripts/migrate.py create "Description"`
3. **Review Migration**: Check the generated migration file in `alembic/versions/`
4. **Test Migration**: Run `make db-upgrade` to apply changes
5. **Commit Changes**: Add migration files to version control

### 2. Production Deployment

1. **Backup Database**: Always backup before migrations
2. **Test Migrations**: Run migrations on staging environment first
3. **Deploy Code**: Deploy new code with migration files
4. **Run Migrations**: Execute `make db-upgrade` in production
5. **Verify**: Check that all tables and data are correct

### 3. Rollback Strategy

1. **Identify Issue**: Determine which migration caused problems
2. **Rollback Code**: Revert to previous code version
3. **Rollback Database**: Run `make db-downgrade` to previous migration
4. **Verify**: Ensure system is working correctly

## Migration Best Practices

### 1. Naming Conventions

- Use descriptive names: `add_user_preferences_table`
- Include action: `add_`, `remove_`, `modify_`, `rename_`
- Be specific: `add_email_index_to_users_table`

### 2. Migration Content

- **Always review** auto-generated migrations
- **Test migrations** on sample data
- **Include data migrations** when needed
- **Add rollback logic** for complex changes

### 3. Data Safety

- **Never drop columns** without data migration
- **Use transactions** for complex operations
- **Backup before** major schema changes
- **Test rollbacks** before production

### 4. Performance Considerations

- **Add indexes** in separate migrations
- **Use batch operations** for large data changes
- **Consider downtime** for major changes
- **Monitor performance** after migrations

## Environment Configuration

### Development
```bash
# Set environment variables
export DATABASE_URL="postgresql://user:password@localhost:5432/guitartab_pro_dev"
export FLASK_DEBUG=True
```

### Production
```bash
# Set environment variables
export DATABASE_URL="postgresql://user:password@prod-server:5432/guitartab_pro"
export FLASK_DEBUG=False
```

## Troubleshooting

### Common Issues

1. **Migration Conflicts**: Resolve by editing migration files
2. **Missing Dependencies**: Ensure all models are imported
3. **Connection Issues**: Check DATABASE_URL environment variable
4. **Permission Errors**: Verify database user permissions

### Recovery Steps

1. **Check Current State**: `python scripts/migrate.py current`
2. **Review History**: `python scripts/migrate.py history`
3. **Manual Fix**: Edit migration files if needed
4. **Re-run Migration**: `python scripts/migrate.py upgrade`

## Monitoring

### Migration Status
- Track migration history in `alembic_version` table
- Monitor migration execution time
- Log migration errors and warnings

### Performance Impact
- Measure query performance before/after migrations
- Monitor database size changes
- Track index usage and effectiveness
