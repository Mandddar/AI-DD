"""
Alembic environment configuration for AI DD.

Supports both sync (for alembic CLI) and async (for programmatic use) migrations.
Imports all module models so Alembic can auto-detect schema changes.
"""
import sys
import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# Add the API root to the path so module imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import Base and ALL models so Alembic sees them
from core.database import Base

# Auth models
from modules.auth.models import User, TokenBlacklist, PasswordResetToken
# Project models
from modules.projects.models import Project, ProjectMember
# DMS models
from modules.dms.models import Document, DocumentText, DocumentTag
# Agent models
from modules.agent.models import AgentRun, AgentFinding, DocumentChunk
# Planning models
from modules.planning.models import AuditPlan, RequestListItem
# Finance models
from modules.finance.models import FinancialDataset, FinancialLineItem, VarianceAnalysis
# Report models
from modules.report.models import Report
# Knowledge models
from modules.knowledge.models import ProjectKnowledge, CrossProjectKnowledge
# Audit models
from modules.audit.models import AuditLog
# Self-improvement models
from modules.self_improvement.models import UsagePattern, ImprovementSuggestion

# Alembic Config object
config = context.config

# Setup logging from alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set target metadata for autogenerate
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode — generates SQL script without DB connection."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode — connects to DB and applies directly."""
    # Use DATABASE_URL env var if set, otherwise fall back to alembic.ini
    url = os.environ.get("DATABASE_URL") or config.get_main_option("sqlalchemy.url")

    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        url=url,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
