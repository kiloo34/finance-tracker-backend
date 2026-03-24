from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import date, datetime
from .models import TransactionType, DebtStatus, GoalStatus, UserRole, UserTier, ObligationType, PocketSort, TxAction

# Base User
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, pattern="^[a-zA-Z0-9_]+$")

class UserCreate(UserBase):
    email: Optional[str] = Field(None, pattern=r'^[^@]+@[^@]+\.[^@]+$')  # optional at registration
    phone_number: Optional[str] = Field(None, pattern=r'^\+?[1-9]\d{1,14}$') # E.164 phone format
    password: str = Field(..., min_length=8, max_length=128)

class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: Optional[str] = None
    phone_number: Optional[str] = None
    role: UserRole
    tier: UserTier
    is_active: bool = True
    created_at: Optional[datetime] = None

# Token
class Token(BaseModel):
    access_token: str
    token_type: str
    role: str
    tier: str
    session_id: Optional[str] = None   # used by frontend to identify current session in Security Center

class TokenData(BaseModel):
    username: Optional[str] = None


# Category
class CategoryBase(BaseModel):
    name: str
    name_en: Optional[str] = None   # English translation
    type: TransactionType
    description: Optional[str] = None

class CategoryCreate(CategoryBase):
    parent_id: Optional[int] = None

class CategoryResponse(CategoryBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    parent_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

class CategoryWithSub(CategoryResponse):
    subcategories: List[CategoryResponse] = []


# Account & Pocket
class AccountBase(BaseModel):
    account_number: str
    owner_name: str

class AccountCreate(AccountBase):
    pass

class AccountResponse(AccountBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    total_balance: float
    created_at: datetime
    updated_at: datetime

class PocketBase(BaseModel):
    pocket_number: str
    name: str
    sort: PocketSort
    currency: str = "IDR"

class PocketCreate(PocketBase):
    account_id: int

class PocketResponse(PocketBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    account_id: int
    balance: float
    created_at: datetime
    updated_at: datetime


# Transaction
class TransactionBase(BaseModel):
    category_id: Optional[int] = None
    amount: float
    action: TxAction
    description: Optional[str] = None
    transaction_date: date
    source_pocket_id: Optional[int] = None
    destination_pocket_id: Optional[int] = None
    actor_id: Optional[int] = None
    resource_type: Optional[str] = None
    resource_id: Optional[int] = None

class TransactionCreate(TransactionBase):
    pass

class TransactionResponse(TransactionBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    category: Optional[CategoryResponse] = None
    source_pocket: Optional[PocketResponse] = None
    destination_pocket: Optional[PocketResponse] = None


# Obligation (Payable & Receivable)
class ObligationBase(BaseModel):
    type: ObligationType
    contact_name: str
    amount: float
    remaining_amount: Optional[float] = None  # defaults to `amount` if not provided
    due_date: Optional[date] = None
    status: DebtStatus = DebtStatus.unpaid
    description: Optional[str] = None

    def model_post_init(self, __context: any) -> None:
        if self.remaining_amount is None:
            self.remaining_amount = self.amount

class ObligationCreate(ObligationBase):
    pass

class ObligationResponse(ObligationBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None


# Financial Goal
class FinancialGoalBase(BaseModel):
    name: str
    target_amount: float
    current_amount: float = 0.0
    target_date: Optional[date] = None
    status: GoalStatus = GoalStatus.in_progress
    description: Optional[str] = None

class FinancialGoalCreate(FinancialGoalBase):
    pass

class FinancialGoalResponse(FinancialGoalBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime


# Budget
class BudgetBase(BaseModel):
    category_id: int
    amount_limit: float
    month: int = Field(..., ge=1, le=12)
    year: int = Field(..., ge=2000)

class BudgetCreate(BudgetBase):
    pass

class BudgetResponse(BudgetBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    # We include category name in the response by extending it dynamically in the router/service if needed
    category: Optional[CategoryResponse] = None


# Notification
class NotificationCreate(BaseModel):
    title: str
    message: str

class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    title: str
    message: str
    status: str
    created_at: datetime


# User Session (for session management / active sessions list)
class UserSessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    user_id: int
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    device_hint: Optional[str] = None
    status: str
    last_seen_at: Optional[datetime] = None
    created_at: datetime
    revoked_at: Optional[datetime] = None


# Audit Log
class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    session_id: Optional[str] = None
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[int] = None
    ip_address: Optional[str] = None
    detail: Optional[str] = None
    created_at: datetime


# Reports
class CategorySummary(BaseModel):
    category_id: Optional[int] = None
    category_name: str
    total_amount: float
    type: str

class ReportSummaryResponse(BaseModel):
    total_income: float
    total_expense: float
    net_savings: float
    expense_ratio: float
    categories: List[CategorySummary]


class FinancialEvaluationResponse(BaseModel):
    total_income: float
    total_expense: float
    saving: float
    expense_ratio_percentage: float
    status: str
