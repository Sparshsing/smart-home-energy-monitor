import os
from fastapi import FastAPI, Depends, HTTPException, APIRouter
from contextlib import asynccontextmanager
from typing import Annotated, Union, List
from sqlalchemy.dialects.postgresql import insert as pg_insert
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import select
from sqlalchemy.exc import ProgrammingError
from sqlalchemy import func, and_, text, literal_column
from datetime import datetime, timedelta, timezone
import uuid
import re

from database import get_session, create_db_and_tables
from sqlmodel.ext.asyncio.session import AsyncSession
from models import Telemetry, TelemetryData, Device, DevicePublic, DeviceEnergySummary, TelemetryBucket
from security import get_current_user, UserClaims

if os.getenv("ENABLE_DEBUGPY") == "true":
    import debugpy
    debugpy.listen(("0.0.0.0", 5679))
    print("Debugpy listening on port 5679. Ready for debugger to attach...")

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Initializing database...")
    await create_db_and_tables()
    yield

app = FastAPI(lifespan=lifespan, title="Telemetry Service API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Adjust for your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

router = APIRouter(prefix="/api/telemetry")

DBSession = Annotated[AsyncSession, Depends(get_session)]
CurrentUserClaims = Annotated[UserClaims, Depends(get_current_user)]

@router.get("/")
async def root():
    return {"message": "Telemetry Service Running"}

@router.get("/health")
async def health_check():
    return {"status": "ok"}

@router.post("/", status_code=201)
async def post_telemetry(
    telemetry_input: TelemetryData,
    session: DBSession
):
    """
    Accepts a single telemetry data point.
    Uses a high-performance insert that ignores duplicates.
    """
    values_to_insert = [telemetry_input.model_dump()]

    # Use SQLAlchemy Core for a high-performance bulk insert.
    stmt = pg_insert(Telemetry).values(values_to_insert)

    # Ignore duplicates on the primary key (device_id, timestamp)
    stmt = stmt.on_conflict_do_nothing(
        index_elements=['device_id', 'timestamp']
    )

    try:
        await session.execute(stmt)
        await session.commit()
        return {"message": "Telemetry data successfully processed."}
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

@router.get("/devices", response_model=List[DevicePublic])
async def get_devices(current_user: CurrentUserClaims, session: DBSession):
    """
    Get a list of all devices registered to the currently authenticated user.
    """
    devices_result = await session.exec(
        select(Device).where(Device.user_id == current_user.user_id)
    )
    devices = devices_result.all()
    return devices

@router.get("/summary", response_model=List[DeviceEnergySummary])
async def get_energy_summary(
    start: datetime,
    end: datetime,
    current_user: CurrentUserClaims,
    session: DBSession
):
    """
    Get a summary of total energy consumed (in kWh) for all devices
    registered to the currently authenticated user within a time range.
    """
    # Energy Used: Avg Power * Actual Data Duration
    # 1. Calculate the actual duration in hours from the first to the last data point
    #    for each device. We use func.extract to get total seconds and convert to hours.
    duration_hours = (
        func.extract('epoch', func.max(Telemetry.timestamp) - func.min(Telemetry.timestamp)) 
        / 3600
    )

    # 2. Calculate the average power (watts) and multiply by the actual duration.
    # Energy (kWh) = Avg Power (W) * Duration (h) / 1000 W/kW
    query = (
        select(
            Device.id,
            Device.name,
            ((func.avg(Telemetry.energy_watts) * duration_hours) / 1000).label("total_kwh"),
        )
        .join(Telemetry, Device.id == Telemetry.device_id)
        .where(
            and_(
                Device.user_id == current_user.user_id,
                Telemetry.timestamp >= start,
                Telemetry.timestamp <= end,
            )
        )
        .group_by(Device.id, Device.name)
    )

    
    result = await session.exec(query)
    summary_data = result.all()

    # Map the SQLAlchemy result (which are KeyedTuples) to the Pydantic model.
    return [
        DeviceEnergySummary(
            device_id=row.id,
            device_name=row.name,
            total_kwh=row.total_kwh or 0.0, # Handle cases where there is no data
        )
        for row in summary_data
    ]

@router.get("/devices/{device_id}", response_model=List[TelemetryBucket])
async def get_device_telemetry(
    device_id: uuid.UUID,
    current_user: CurrentUserClaims,
    session: DBSession,
    start: datetime,
    end: datetime,
    interval: str = "1h",
):
    """
    Get time-series data for a specific device, bucketed into time intervals.
    `interval` can be '1m', '5m', '1h', '1d', etc.
    """
    # 1. Verify the device belongs to the user
    device_result = await session.exec(
        select(Device).where(Device.id == device_id, Device.user_id == current_user.user_id)
    )
    device = device_result.first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found or access denied.")

    # 2. Get the bucketed telemetry data
    # We must validate the interval to prevent SQL injection before using it in a literal_column.
    if not re.match(r"^\d+\s*\w+$", interval):
        raise HTTPException(status_code=400, detail="Invalid interval format.")

    # We use func.time_bucket from SQLAlchemy to call the TimescaleDB-specific function.
    # Using literal_column is necessary to properly construct the interval cast.
    query = (
        select(
            func.time_bucket(literal_column(f"'{interval}'"), Telemetry.timestamp).label("bucket"),
            func.avg(Telemetry.energy_watts).label("avg_watts"),
        )
        .where(
            and_(
                Telemetry.device_id == device_id,
                Telemetry.timestamp >= start,
                Telemetry.timestamp <= end,
            )
        )
        .group_by("bucket")
        .order_by("bucket")
    )
    
    result = await session.exec(query)
    
    return [
        TelemetryBucket(bucket=row.bucket, avg_watts=row.avg_watts or 0.0)
        for row in result.all()
    ]


app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8002, reload=True)