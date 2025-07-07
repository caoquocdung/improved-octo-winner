from typing import List, Optional
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import (
    Float,
    ForeignKey,
    String,
    Integer,
    Boolean,
    DateTime,
    Enum as SAEnum,
    Text,
)
import enum
from datetime import datetime, timezone


class UserRole(enum.Enum):
    USER = "user"
    TEAM = "team"
    ADMIN = "admin"


class UserStatus(enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ANONYMIZED = "anonymized"
    BANNED = "banned"


class ApproveStatus(enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class NotificationType(enum.Enum):
    NEW_STORY = "new_story"
    NEW_CHAPTER = "new_chapter"
    ADMIN_FEEDBACK = "admin_feedback"
    DONATE = "donate"
    OTHER = "other"


class Base(DeclarativeBase):
    pass


# --------------- User ---------------
class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    group_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("groups.id"), nullable=True
    )
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    email: Mapped[Optional[str]] = mapped_column(
        String(255), unique=True, index=True, nullable=True
    )
    hashed_password: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    role: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole), default=UserRole.USER, nullable=False
    )
    status: Mapped[UserStatus] = mapped_column(
        SAEnum(UserStatus), default=UserStatus.ACTIVE
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    comments: Mapped[List["Comment"]] = relationship(
        back_populates="user"
    )  # Có thể bỏ cascade nếu muốn giữ lại comment khi user xóa
    donates: Mapped[List["Donate"]] = relationship(
        back_populates="user"
    )  # Tùy, thường nên để cascade, hoặc kiểm soát khi xóa/anonymize
    follows: Mapped[List["Follow"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    notifications: Mapped[List["Notification"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    group: Mapped[Optional["Group"]] = relationship(back_populates="members")


# --------------- Group ---------------
class Group(Base):
    __tablename__ = "groups"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    avatar: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    members: Mapped[List["User"]] = relationship(back_populates="group")
    # Quan hệ n-n: các truyện mà group này dịch
    stories: Mapped[List["GroupStory"]] = relationship(
        back_populates="group", cascade="all, delete-orphan"
    )
    chapters: Mapped[List["Chapter"]] = relationship(
        back_populates="group", cascade="all, delete-orphan"
    )
    donates: Mapped[List["Donate"]] = relationship(
        back_populates="group", cascade="all, delete-orphan"
    )


# --------------- UserGroup ---------------
class UserGroup(Base):
    __tablename__ = "user_group"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"))
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    user: Mapped["User"] = relationship()
    group: Mapped["Group"] = relationship()


# --------------- Story ---------------
class Story(Base):
    __tablename__ = "stories"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255), index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tags: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    author: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    status: Mapped[ApproveStatus] = mapped_column(
        SAEnum(ApproveStatus), default=ApproveStatus.PENDING
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    groups: Mapped[List["GroupStory"]] = relationship(
        back_populates="story", cascade="all, delete-orphan"
    )
    chapters: Mapped[List["Chapter"]] = relationship(
        back_populates="story", cascade="all, delete-orphan"
    )
    comments: Mapped[List["Comment"]] = relationship(
        back_populates="story", cascade="all, delete-orphan"
    )
    follows: Mapped[List["Follow"]] = relationship(
        back_populates="story", cascade="all, delete-orphan"
    )
    donates: Mapped[List["Donate"]] = relationship(
        back_populates="story", cascade="all, delete-orphan"
    )


# --------------- GroupStory (N-N group <-> story) ---------------
class GroupStory(Base):
    __tablename__ = "group_story"
    id: Mapped[int] = mapped_column(primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"))
    story_id: Mapped[int] = mapped_column(ForeignKey("stories.id"))
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    group: Mapped["Group"] = relationship(back_populates="stories")
    story: Mapped["Story"] = relationship(back_populates="groups")


# --------------- Chapter ---------------
class Chapter(Base):
    __tablename__ = "chapters"
    id: Mapped[int] = mapped_column(primary_key=True)
    story_id: Mapped[int] = mapped_column(ForeignKey("stories.id"))
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"))
    number: Mapped[int] = mapped_column(Integer)
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    images: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[ApproveStatus] = mapped_column(
        SAEnum(ApproveStatus), default=ApproveStatus.PENDING
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    story: Mapped["Story"] = relationship(back_populates="chapters")
    group: Mapped["Group"] = relationship(back_populates="chapters")
    comments: Mapped[List["Comment"]] = relationship(
        back_populates="chapter", cascade="all, delete-orphan"
    )


# --------------- Comment ---------------
class Comment(Base):
    __tablename__ = "comments"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    story_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("stories.id"), nullable=True
    )
    group_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("groups.id"), nullable=True
    )
    chapter_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("chapters.id"), nullable=True
    )
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    user: Mapped["User"] = relationship(back_populates="comments")
    story: Mapped[Optional["Story"]] = relationship(back_populates="comments")
    group: Mapped[Optional["Group"]] = relationship()
    chapter: Mapped[Optional["Chapter"]] = relationship(back_populates="comments")


# --------------- Follow ---------------
class Follow(Base):
    __tablename__ = "follows"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    story_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("stories.id"), nullable=True
    )
    group_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("groups.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    user: Mapped["User"] = relationship(back_populates="follows")
    story: Mapped[Optional["Story"]] = relationship(back_populates="follows")
    group: Mapped[Optional["Group"]] = relationship()


# --------------- Notification ---------------
class Notification(Base):
    __tablename__ = "notifications"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    type: Mapped[NotificationType] = mapped_column(
        SAEnum(NotificationType), default=NotificationType.OTHER
    )
    content: Mapped[str] = mapped_column(Text)
    link: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    user: Mapped["User"] = relationship(back_populates="notifications")


# --------------- Donate ---------------
class Donate(Base):
    __tablename__ = "donates"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    group_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("groups.id"), nullable=True
    )
    story_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("stories.id"), nullable=True
    )
    amount: Mapped[float] = mapped_column(Float)
    message: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    user: Mapped["User"] = relationship(back_populates="donates")
    group: Mapped[Optional["Group"]] = relationship(back_populates="donates")
    story: Mapped[Optional["Story"]] = relationship(back_populates="donates")
