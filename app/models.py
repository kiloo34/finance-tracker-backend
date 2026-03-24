"""
SQLAlchemy ORM Models — Finance Tracker

Best Practices Applied:
- Numeric(15, 2) for all monetary amounts (never Float — imprecise for finance)
- DateTime(timezone=True) everywhere — stores in UTC, safe across timezones
- func.now() for server defaults — portable across PostgreSQL, SQLite, MySQL
- __table_args__ with Index and CheckConstraint for query performance and data integrity
- Consistent nullable=False on required columns
- Proper relationships defined on all models
- No duplicate column definitions
- user_agent stored as Text (unlimited) to avoid browser string truncation
- audit_logs.detail stored as Text (unlimited JSON)
"""

from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Text, Numeric, ForeignKey, Date,
    DateTime, Enum as SQLEnum, Boolean, Index, CheckConstraint,
    func
)
from sqlalchemy.orm import relationship
import enum
from .database import Base


# ── Enumerations ────────────────────────────────────────────────────────────


class UserRole(str, enum.Enum):
    admin = 'admin'
    user = 'user'


class UserTier(str, enum.Enum):
    regular = 'regular'
    premium = 'premium'


class TransactionType(str, enum.Enum):
    income = 'income'
    expense = 'expense'


class ObligationType(str, enum.Enum):
    payable = 'payable'      # Money user OWES (was Debt)
    receivable = 'receivable' # Money OWED to user (was Receivable)


class DebtStatus(str, enum.Enum):
    unpaid = 'unpaid'
    partially_paid = 'partially_paid'
    paid = 'paid'


class GoalStatus(str, enum.Enum):
    in_progress = 'in_progress'
    completed = 'completed'
    cancelled = 'cancelled'


class NotificationStatus(str, enum.Enum):
    unread = 'unread'
    read = 'read'


class SessionStatus(str, enum.Enum):
    active = 'active'
    revoked = 'revoked'
    expired = 'expired'


class PocketSort(str, enum.Enum):
    saving = 'saving'
    spending = 'spending'
    sharing = 'sharing'


class TxAction(str, enum.Enum):
    income = 'income'
    expense = 'expense'
    transfer = 'transfer'
    saving = 'saving'


# ── Models ──────────────────────────────────────────────────────────────────


class User(Base):
    """
    Core user account. Stores credentials, role, tier, and account state.
    email is optional for now — reserved for future OAuth/email-login support.
    """
    __tablename__ = "users"
    __table_args__ = (
        Index("ix_users_username", "username"),
        Index("ix_users_email", "email"),
        Index("ix_users_phone_number", "phone_number"),
    )

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=True)    # optional login field
    phone_number = Column(String(20), unique=True, nullable=True)  # optional login field
    hashed_password = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.user, nullable=False)
    tier = Column(SQLEnum(UserTier), default=UserTier.regular, nullable=False)
    is_active = Column(Boolean, default=True, server_default='true', nullable=False)  # soft-delete / disable account
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")


class Category(Base):
    """User-defined transaction categories (e.g. 'Groceries', 'Salary')."""
    __tablename__ = "categories"
    __table_args__ = (
        Index("ix_categories_user_id", "user_id"),
        Index("ix_categories_user_type", "user_id", "type"),
        Index("ix_categories_parent_id", "parent_id"),
    )

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    parent_id = Column(Integer, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True) # For subcategories
    name = Column(String(100), nullable=False)           # Indonesian (default)
    name_en = Column(String(100), nullable=True)         # English translation
    type = Column(SQLEnum(TransactionType, name="transaction_type"), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user = relationship("User")
    parent = relationship("Category", remote_side=[id], back_populates="subcategories")
    subcategories = relationship("Category", back_populates="parent")


class Account(Base):
    """User bank or cash accounts."""
    __tablename__ = "accounts"
    __table_args__ = (
        Index("ix_accounts_user_id", "user_id"),
        Index("ix_accounts_number", "account_number", unique=True),
    )

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    account_number = Column(String(50), nullable=False)
    owner_name = Column(String(100), nullable=False)
    total_balance = Column(Numeric(15, 2), default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user = relationship("User")
    pockets = relationship("Pocket", back_populates="account", cascade="all, delete-orphan")


class Pocket(Base):
    """Sub-accounts (pockets) for partitioning funds within an Account."""
    __tablename__ = "pockets"
    __table_args__ = (
        Index("ix_pockets_account_id", "account_id"),
        Index("ix_pockets_number", "pocket_number", unique=True),
    )

    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False)
    pocket_number = Column(String(50), nullable=False)
    name = Column(String(100), nullable=False)
    sort = Column(SQLEnum(PocketSort), default=PocketSort.spending, nullable=False)
    currency = Column(String(10), default='IDR', nullable=False)
    balance = Column(Numeric(15, 2), default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    account = relationship("Account", back_populates="pockets")


class Transaction(Base):
    """
    Financial transaction record. Modified to support accounts/pockets and transfers.
    """
    __tablename__ = "transactions"
    __table_args__ = (
        Index("ix_transactions_user_id", "user_id"),
        Index("ix_transactions_user_date", "user_id", "transaction_date"),
        Index("ix_transactions_action", "action"),
        Index("ix_transactions_source_pocket", "source_pocket_id"),
        Index("ix_transactions_dest_pocket", "destination_pocket_id"),
        CheckConstraint("amount > 0", name="ck_transactions_amount_positive"),
    )

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    actor_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True) # Who performed the TX
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True)
    
    source_pocket_id = Column(Integer, ForeignKey("pockets.id", ondelete="SET NULL"), nullable=True)
    destination_pocket_id = Column(Integer, ForeignKey("pockets.id", ondelete="SET NULL"), nullable=True)
    
    amount = Column(Numeric(15, 2), nullable=False)
    action = Column(SQLEnum(TxAction), nullable=False) # Normalized type
    description = Column(Text, nullable=True)
    transaction_date = Column(Date, nullable=False)
    
    # Old fields kept for minimal compatibility during migration if needed, but deprecated
    type = Column(SQLEnum(TransactionType, name="transaction_type"), nullable=True)
    resource_type = Column(String(50), nullable=True)
    resource_id = Column(Integer, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    category = relationship("Category")
    user = relationship("User", foreign_keys=[user_id])
    actor = relationship("User", foreign_keys=[actor_id])
    source_pocket = relationship("Pocket", foreign_keys=[source_pocket_id])
    destination_pocket = relationship("Pocket", foreign_keys=[destination_pocket_id])


class Obligation(Base):
    """
    Unified model for both money user OWES (Payable/Debt) 
    and money someone OWES to user (Receivable).
    """
    __tablename__ = "obligations"
    __table_args__ = (
        Index("ix_obligations_user_id", "user_id"),
        Index("ix_obligations_user_type", "user_id", "type"),
        Index("ix_obligations_user_status", "user_id", "status"),
        CheckConstraint("amount > 0", name="ck_obligations_amount_positive"),
        CheckConstraint("remaining_amount >= 0", name="ck_obligations_remaining_non_negative"),
        CheckConstraint("remaining_amount <= amount", name="ck_obligations_remaining_lte_amount"),
    )

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    type = Column(SQLEnum(ObligationType, name="obligation_type"), nullable=False)
    contact_name = Column(String(100), nullable=False)  # Debtor or Creditor name
    amount = Column(Numeric(15, 2), nullable=False)
    remaining_amount = Column(Numeric(15, 2), nullable=False)
    due_date = Column(Date, nullable=True)
    status = Column(SQLEnum(DebtStatus, name="debt_status"), default=DebtStatus.unpaid, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User")


class FinancialGoal(Base):
    """
    A savings or financial target the user is working toward.
    Progress tracked via current_amount vs target_amount.
    """
    __tablename__ = "financial_goals"
    __table_args__ = (
        Index("ix_financial_goals_user_id", "user_id"),
        Index("ix_financial_goals_user_status", "user_id", "status"),
        CheckConstraint("target_amount > 0", name="ck_goals_target_positive"),
        CheckConstraint("current_amount >= 0", name="ck_goals_current_non_negative"),
    )

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    target_amount = Column(Numeric(15, 2), nullable=False)          # was Float — fixed
    current_amount = Column(Numeric(15, 2), default=0, nullable=False) # was Float — fixed; removed duplicate
    target_date = Column(Date, nullable=True)
    status = Column(SQLEnum(GoalStatus, name="goal_status"), default=GoalStatus.in_progress, nullable=False)
    description = Column(Text, nullable=True)                        # was duplicated — fixed
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user = relationship("User")


class Notification(Base):
    """
    In-app notifications generated by the system (e.g. overspending alerts).
    Indexed on (user_id, status) for fast unread-count queries.
    """
    __tablename__ = "notifications"
    __table_args__ = (
        Index("ix_notifications_user_id", "user_id"),
        Index("ix_notifications_user_status", "user_id", "status"),  # fast unread count
    )

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    status = Column(SQLEnum(NotificationStatus), default=NotificationStatus.unread, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User")


class Budget(Base):
    """
    Monthly spending limit for a specific category.
    """
    __tablename__ = "budgets"
    __table_args__ = (
        Index("ix_budgets_user_id", "user_id"),
        Index("ix_budgets_user_category_period", "user_id", "category_id", "month", "year", unique=True),
        CheckConstraint("amount_limit > 0", name="ck_budgets_limit_positive"),
        CheckConstraint("month >= 1 AND month <= 12", name="ck_budgets_month_valid"),
        CheckConstraint("year >= 2000", name="ck_budgets_year_valid"),
    )

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="CASCADE"), nullable=False)
    amount_limit = Column(Numeric(15, 2), nullable=False)
    month = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user = relationship("User")
    category = relationship("Category")


class UserSession(Base):
    """
    Tracks each login session: device, IP, and revocation state.
    The `id` is a UUID string used as the JWT `jti` claim.
    """
    __tablename__ = "user_sessions"
    __table_args__ = (
        Index("ix_user_sessions_user_id", "user_id"),
        Index("ix_user_sessions_user_status", "user_id", "status"),  # fast active-session queries
    )

    id = Column(String(64), primary_key=True)                # UUID — used as JWT jti
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    ip_address = Column(String(64), nullable=True)
    user_agent = Column(Text, nullable=True)                 # was String(512) — upgraded to Text
    device_hint = Column(String(128), nullable=True)         # e.g. "💻 macOS — Chrome"
    status = Column(SQLEnum(SessionStatus), default=SessionStatus.active, nullable=False)
    last_seen_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    revoked_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="sessions")


class AuditLog(Base):
    """
    Immutable append-only record of every significant user action.
    Never update or delete rows — only insert.
    Composite index on (user_id, created_at) supports paginated queries efficiently.
    """
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_audit_logs_user_id", "user_id"),
        Index("ix_audit_logs_user_created", "user_id", "created_at"),  # pagination index
        Index("ix_audit_logs_action", "action"),
    )

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    session_id = Column(String(64), nullable=True)           # which session triggered this
    action = Column(String(100), nullable=False)             # e.g. "transaction.create"
    resource_type = Column(String(50), nullable=True)        # e.g. "Transaction"
    resource_id = Column(Integer, nullable=True)             # e.g. the transaction id
    ip_address = Column(String(64), nullable=True)
    detail = Column(Text, nullable=True)                     # was String(500) — upgraded to Text
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User", back_populates="audit_logs")
