"""
Database models and session management for PostgreSQL.
"""
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timezone

from app.core.config import settings

# Create database engine
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def utc_now():
    """Return current UTC time as timezone-aware datetime."""
    return datetime.now(timezone.utc)


class TLECache(Base):
    """TLE cache table for storing satellite orbital data."""
    __tablename__ = "tle_cache"
    
    norad_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    tle_line1 = Column(String(255), nullable=False)
    tle_line2 = Column(String(255), nullable=False)
    satellite_group = Column(String(100), nullable=False, index=True)
    fetched_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    extra_data = Column(Text, nullable=True)  # Renamed from 'metadata' to avoid SQLAlchemy reserved name


class Schedule(Base):
    """Schedule table for approved/overridden passes."""
    __tablename__ = "schedules"
    
    id = Column(String(255), primary_key=True)
    satellite_id = Column(Integer, nullable=False, index=True)
    ground_station_id = Column(Integer, nullable=False, index=True)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    max_elevation_deg = Column(Float, nullable=False)
    status = Column(String(50), nullable=False)
    approved = Column(Boolean, default=False)
    override_reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)


class Conflict(Base):
    """Conflicts table for tracking scheduling conflicts."""
    __tablename__ = "conflicts"
    
    id = Column(String(255), primary_key=True)
    ground_station_id = Column(Integer, nullable=False, index=True)
    pass_ids = Column(Text, nullable=False)  # JSON array as text
    overlap_start = Column(DateTime(timezone=True), nullable=False)
    overlap_end = Column(DateTime(timezone=True), nullable=False)
    resolved = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=utc_now)


class Recommendation(Base):
    """Recommendations table for AI-generated conflict resolutions."""
    __tablename__ = "recommendations"
    
    id = Column(String(255), primary_key=True)
    conflict_id = Column(String(255), nullable=False, index=True)
    suggested_action = Column(String(100), nullable=False)
    target_pass_id = Column(String(255), nullable=True)
    alternative_window = Column(Text, nullable=True)  # JSON as text
    reasoning = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now)


def get_db():
    """Dependency for getting database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)
