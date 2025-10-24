import datetime as dt
from typing import List

from sqlalchemy import (
    TIMESTAMP, DATE, Interval, ForeignKey, Float, Integer, String, Text, func, UniqueConstraint, BigInteger
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass

class AppUser(Base):
    __tablename__ = "app_user"

    user_id:          Mapped[str] = mapped_column(String, primary_key=True)
    polar_user_id:    Mapped[str] = mapped_column(String, nullable=False)
    created_at:       Mapped[dt.datetime] = mapped_column(TIMESTAMP(timezone=True),
                                                                 default=func.now(),
                                                                 nullable=False)
    updated_at:       Mapped[dt.datetime] = mapped_column(TIMESTAMP(timezone=True),
                                                                 default=func.now(),
                                                                 onupdate=func.now(),
                                                                 nullable=False)
    # One-to-one relationship with access token
    access_token: Mapped["AccessToken"] = relationship(
        uselist=False,
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="selectin"
    )

    # One-to-many relationship with daily summary, indicated with Mapped[List[<table_name>]]
    daily_summaries: Mapped[List["ActivitySummary"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="selectin"
    )

    # One-to-many relationship with step, indicated with Mapped[List[<table_name>]]
    steps: Mapped[List["StepSample"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="selectin"
    )


class AccessToken(Base):
    __tablename__ = 'access_token'

    user_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("app_user.user_id", ondelete="CASCADE"),
        nullable=False,
        primary_key=True
    )
    access_token: Mapped[str] = mapped_column(Text)
    issuer: Mapped[str] = mapped_column(Text, nullable=False)
    issued_at: Mapped[dt.datetime] = mapped_column(TIMESTAMP(timezone=True),
                                                          server_default=func.now(),
                                                          nullable=False)
    updated_at: Mapped[dt.datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    expires_at: Mapped[dt.datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)

    user: Mapped["AppUser"] = relationship(back_populates="access_token", single_parent=True, lazy="selectin")

    __table_args__ = (UniqueConstraint("user_id"),)


class ActivitySummary(Base):
    __tablename__ = "activity_summary"

    user_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("app_user.user_id", ondelete="CASCADE"),
        nullable=False,
        primary_key=True
    )
    date:    Mapped[dt.date] = mapped_column(DATE, nullable=False, primary_key=True)

    start_time:       Mapped[dt.datetime | None] = mapped_column(TIMESTAMP(timezone=True))
    end_time:         Mapped[dt.datetime | None] = mapped_column(TIMESTAMP(timezone=True))
    active_duration:  Mapped[dt.timedelta | None] = mapped_column(Interval)
    inactive_duration:Mapped[dt.timedelta | None] = mapped_column(Interval)

    daily_activity:   Mapped[float | None] = mapped_column(Float)
    calories:         Mapped[int | None] = mapped_column(Integer)
    active_calories:  Mapped[int | None] = mapped_column(Integer)
    steps:            Mapped[int | None] = mapped_column(Integer)
    inactivity_alert_count: Mapped[int | None] = mapped_column(Integer)
    distance_from_steps:    Mapped[float | None] = mapped_column(Float)

    created_at: Mapped[dt.datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[dt.datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # Backref to parent: app_user
    user: Mapped["AppUser"] = relationship(back_populates="daily_summaries", lazy="selectin")


class StepSample(Base):
    __tablename__ = "step_sample"

    __table_args__ = ({
        'timescaledb_hypertable': {
            'time_column_name': 'timestamp'
        }
    })
    sample_id: Mapped[int] = mapped_column(BigInteger, autoincrement=True, primary_key=True)
    user_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("app_user.user_id", ondelete="CASCADE")
    )
    timestamp: Mapped[dt.datetime] = mapped_column(TIMESTAMP(timezone=True))
    steps: Mapped[int] = mapped_column(Integer, nullable=False)

    # Backref to parent: app_user
    user: Mapped["AppUser"] = relationship(back_populates="steps", lazy="selectin")
