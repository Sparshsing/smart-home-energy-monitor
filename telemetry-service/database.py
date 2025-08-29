import asyncio
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from typing import AsyncGenerator

from config import settings

# Create an async engine, which is the correct way for async FastAPI
engine = create_async_engine(settings.DATABASE_URL, echo=True)

async def create_db_and_tables(max_retries: int = 3, base_delay_seconds: float = 5.0):
    attempt = 1
    while True:
        try:
            async with engine.begin() as conn:
                # 1) Ensure TimescaleDB extension (once per database)
                await conn.exec_driver_sql("CREATE EXTENSION IF NOT EXISTS timescaledb;")

                # 2) Create ORM tables we own (exclude stub-only tables)
                #    Use create_all with include_tables to avoid creating the external 'user' table stub.
                from models import Product, Device, Telemetry
                await conn.run_sync(
                    SQLModel.metadata.create_all,
                    tables=[Product.__table__, Device.__table__, Telemetry.__table__],
                )

                # 3) Convert telemetry into a hypertable (idempotent)
                await conn.exec_driver_sql(
                    "SELECT create_hypertable('telemetry','timestamp', if_not_exists => TRUE);"
                )

            print("Database init complete: extension ensured, tables created, hypertable ensured.")
            break
        except Exception as e:
            if attempt >= max_retries:
                print(f"Database init failed after {attempt} attempts: {e}")
                raise
            sleep_seconds = base_delay_seconds * (2 ** (attempt - 1))
            if sleep_seconds > 30:
                sleep_seconds = 30
            print(
                f"Database init attempt {attempt}/{max_retries} failed: {e}. "
                f"Retrying in {sleep_seconds} seconds..."
            )
            await asyncio.sleep(sleep_seconds)
            attempt += 1

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session
