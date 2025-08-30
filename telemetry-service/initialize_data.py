import asyncio
import random
import uuid
from datetime import datetime, timedelta, timezone
from typing import List

import httpx
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from database import engine
from models import Product, Device, user_table
from sqlalchemy import select as sa_select


TELEMETRY_API_BASE = "http://localhost:8002/api/telemetry"


async def register_devices(user_id: int, num_devices: int = 5) -> List[dict]:
    """Create sample products and devices for a user. Idempotent.
    """
    async with AsyncSession(engine) as session:
        # check if user exists
        user_check = await session.exec(
            sa_select(user_table.c.id).where(user_table.c.id == user_id)
        )
        if not user_check.first():
            raise ValueError(f"User with id {user_id} does not exist. Aborting seeding.")

        # Create products
        products_to_create = [
            {"name": "Smart Plug", "type": "Smart Plug", "description": "Smart Plug 10Amp"},
            {"name": "Air Conditioner", "type": "Air Conditioner", "description": "12000 BTU smart AC unit."},
            {"name": "Smart Fan", "type": "Smart Fan", "description": "Smart Fan 100W"},
            {"name": "Smart Light", "type": "Smart Light", "description": "Smart Light 100W"},
            {"name": "Smart Fridge", "type": "Smart Fridge", "description": "Smart Fridge 3 Star"},
        ]

        product_ids: dict[str, int] = {}
        for product_data in products_to_create:
            result = await session.exec(select(Product).where(Product.name == product_data["name"]))
            product = result.first()
            if not product:
                product = Product.model_validate(product_data)
                session.add(product)
                await session.commit()
                await session.refresh(product)
                print(f"  - Created product: {product.name}")
            product_ids[product.name] = product.id  # type: ignore[arg-type]

        # Create devices
        devices: List[Device] = []
        # Start numbering at 1 per product
        product_device_count = {product_id: 1 for product_id in product_ids.values()}
        product_name_choices = list(product_ids.keys())
        for i in range(1, num_devices + 1):
            chosen_product_name = random.choice(product_name_choices)
            chosen_product_id = product_ids[chosen_product_name]
            # Find the next available name for this product and user
            next_index = product_device_count[chosen_product_id]
            while True:
                device_name = f"{chosen_product_name} - {next_index}"
                result = await session.exec(
                    select(Device).where(
                        Device.user_id == user_id,
                        Device.name == device_name,
                    )
                )
                if not result.first():
                    break
                next_index += 1
            product_device_count[chosen_product_id] = next_index + 1

            device = Device(name=device_name, user_id=user_id, product_id=chosen_product_id)
            session.add(device)
            await session.commit()
            await session.refresh(device)
            print(f"  - Created device {i}: {device.name}")
            devices.append({'id': device.id, 'name': device.name})

        return devices


async def ingest_device_telemetry(client: httpx.AsyncClient, device_id: uuid.UUID, start: datetime, duration_hours: int = 24):
    """Send one reading per minute for the given duration starting from 'start'."""
    total_seconds = duration_hours * 60 * 60
    for t in range(0, total_seconds, 60):
        ts = (start + timedelta(seconds=t)).isoformat().replace("+00:00", "Z")
        payload = {
            "device_id": str(device_id),
            "timestamp": ts,
            "energy_watts": random.uniform(5, 250),
        }
        try:
            resp = await client.post(TELEMETRY_API_BASE + "/", json=payload, timeout=10.0)
            if resp.status_code >= 300:
                print(f"    Post failed for {device_id} at {ts}: {resp.status_code} {resp.text}")
        except Exception as exc:
            print(f"    Exception posting telemetry for {device_id} at {ts}: {exc}")
        # Throttle a bit to avoid overwhelming during local dev
        await asyncio.sleep(0.01)


async def main():
    print("Initializing sample products/devices and ingesting telemetry...")

    user_id = 1
    devices = await register_devices(user_id=user_id, num_devices=5)

    # Ingest data for each device concurrently
    start_of_today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    async with httpx.AsyncClient() as client:
        tasks = [
            ingest_device_telemetry(client, device['id'], start=start_of_today, duration_hours=24)  # type: ignore[arg-type]
            for device in devices
        ]
        for device in devices:
            print(f"Simulating device {device['name']} {device['id']}")
        await asyncio.gather(*tasks)
    print("Telemetry ingestion complete.")


if __name__ == "__main__":
    asyncio.run(main())