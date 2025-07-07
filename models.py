from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Integer, Boolean, DateTime, Enum as SAEnum
import enum
from datetime import datetime, timezone

class UserRole(enum.Enum):
    USER = "user"
    TEAM = "team"
    ADMIN = "admin"

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=True)  # nullable cho anonymize
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=True)  # nullable cho anonymize
    role: Mapped[UserRole] = mapped_column(SAEnum(UserRole), default=UserRole.USER, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    anonymized: Mapped[bool] = mapped_column(Boolean, default=False)
