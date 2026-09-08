import os
from datetime import datetime, timezone
from sqlalchemy import create_engine, String, JSON, DateTime, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from sqlalchemy.pool import StaticPool

DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./control-plane.db')
if os.getenv('VERCEL') and not os.getenv('DATABASE_URL'):
    # Vercel functions run with an ephemeral, read-only filesystem. Keep the
    # demo API usable there with an in-memory database; production should set
    # DATABASE_URL to a managed PostgreSQL instance.
    DATABASE_URL = 'sqlite://'
    engine = create_engine(
        DATABASE_URL,
        connect_args={'check_same_thread': False},
        poolclass=StaticPool,
        pool_pre_ping=True,
    )
else:
    engine = create_engine(
        DATABASE_URL,
        connect_args={'check_same_thread': False} if DATABASE_URL.startswith('sqlite') else {},
        pool_pre_ping=True,
    )
Session = sessionmaker(engine, expire_on_commit=False)
class Base(DeclarativeBase): pass
class Record(Base):
    __tablename__ = 'records'
    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    kind: Mapped[str] = mapped_column(String(50), index=True)
    data: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
class Secret(Base):
    __tablename__ = 'secrets'
    id: Mapped[str] = mapped_column(String(200), primary_key=True)
    project: Mapped[str] = mapped_column(String(100), index=True)
    environment: Mapped[str] = mapped_column(String(30))
    name: Mapped[str] = mapped_column(String(100))
    ciphertext: Mapped[str] = mapped_column(Text)
Base.metadata.create_all(engine)
