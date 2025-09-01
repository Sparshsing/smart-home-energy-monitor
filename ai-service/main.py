import os
from fastapi import FastAPI, Depends, HTTPException, APIRouter, Body
from typing import Annotated, List
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from dotenv import load_dotenv

from models import QueryResponse
import httpx
from query_helper import get_system_prompt, get_sql_query, generate_final_response, get_llm_model_and_api_key

load_dotenv()

if os.getenv("ENABLE_DEBUGPY") == "true":
    import debugpy
    debugpy.listen(("0.0.0.0", 5680))
    print("Debugpy listening on port 5680. Waiting for debugger to attach...")


TELEMETRY_SERVICE_URL = os.getenv("TELEMETRY_SERVICE_URL", "http://telemetry-service:8002/api/telemetry")

app = FastAPI(title="AI Service API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Adjust for your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

router = APIRouter(prefix="/api/ai")

# CurrentUserClaims = Annotated[UserClaims, Depends(get_current_user)]

http_bearer = HTTPBearer()


@app.get("/")
async def root():
    return {"message": "AI Service Running"}


@router.get("/health")
async def health_check():
    return {"status": "ok"}


async def get_user_devices_from_telemetry(token: str) -> List[dict]:
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {token}"}
        try:
            response = await client.get(f"{TELEMETRY_SERVICE_URL}/devices/details", headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=f"Error fetching devices: {e.response.text}")
        except httpx.RequestError as e:
            raise HTTPException(status_code=500, detail=f"Request to telemetry service failed: {e}")


async def execute_query_on_telemetry(query: str, token: str) -> dict:
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {token}"}
        try:
            response = await client.post(f"{TELEMETRY_SERVICE_URL}/query", json={"query": query}, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=f"Error executing query: {e.response.text}")
        except httpx.RequestError as e:
            raise HTTPException(status_code=500, detail=f"Request to telemetry service failed: {e}")


@router.post("/query", response_model=QueryResponse)
async def get_telemetry_query_answer(
    user_query: str,
    token: str = Depends(http_bearer),
):
    """
    Provide answer to a natural language query from the user, by executing a SQL query and synthesizing the response.
    """
    # 1. Get user devices from telemetry service
    device_details = await get_user_devices_from_telemetry(token.credentials)
    if not device_details:
        return QueryResponse(answer="You don't have any devices registered.", sql_query=None, results=None)

    # 2. Generate SQL query from natural language
    try:
        model_name, api_key = get_llm_model_and_api_key()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Query Service not available. LLM API Key not found.")
    
    system_prompt = get_system_prompt(device_details)
    sql_query = await get_sql_query(user_query, system_prompt, model_name, api_key)
    
    # 3. Execute SQL query on telemetry service
    results = await execute_query_on_telemetry(sql_query, token.credentials)
    
    # 4. Generate final response
    answer = await generate_final_response(user_query, sql_query, results, device_details, model_name, api_key)
    
    return QueryResponse(answer=answer, sql_query=sql_query, results=results)


app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8003, reload=True)