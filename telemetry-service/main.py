import os
from fastapi import FastAPI, Depends, HTTPException, APIRouter
from contextlib import asynccontextmanager
from typing import Annotated, Union, List
from sqlalchemy.dialects.postgresql import insert as pg_insert
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import select
from sqlalchemy.exc import ProgrammingError
from database import get_session, create_db_and_tables
from sqlmodel.ext.asyncio.session import AsyncSession
from models import Telemetry, TelemetryData, Device, DevicePublic
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

app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8002, reload=True)