import uuid
from datetime import datetime, timezone
from typing import Optional, List

from sqlmodel import Field, SQLModel, Relationship
from sqlalchemy import Table, Column, Integer, DateTime
from pydantic import BaseModel

# Forward reference for relationships
class Device:
    pass

class Product(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=50)
    type: str = Field(max_length=50)
    description: Optional[str] = None
    
    devices: List["Device"] = Relationship(back_populates="product")

# Lightweight external-table stub to satisfy FK resolution without owning creation
# During DB initialization, this table needs to be skipped (SQLModel.metadata.create_all).
user_table = Table(
    "user",
    SQLModel.metadata,
    Column("id", Integer, primary_key=True),
)

class Device(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(max_length=50)
    user_id: int = Field(foreign_key="user.id", index=True)
    product_id: int = Field(foreign_key="product.id", index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc),
                                 sa_column=Column(DateTime(timezone=True), nullable=False))
    
    product: "Product" = Relationship(back_populates="devices")

class Telemetry(SQLModel, table=True):
    timestamp: datetime = Field(sa_column=Column(DateTime(timezone=True), primary_key=True))
    device_id: uuid.UUID = Field(foreign_key="device.id", primary_key=True)
    energy_watts: float

# Pydantic models for API data validation
class TelemetryData(BaseModel):
    device_id: uuid.UUID
    timestamp: datetime
    energy_watts: float

class DevicePublic(BaseModel):
    id: uuid.UUID
    name: str
    product_id: int
    created_at: datetime

# New models for analytics endpoints
class DeviceEnergySummary(BaseModel):
    device_id: uuid.UUID
    device_name: str
    total_kwh: float

class TelemetryBucket(BaseModel):
    bucket: datetime
    avg_watts: float

class QueryRequest(BaseModel):
    query: str