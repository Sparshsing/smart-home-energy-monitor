from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Telemetry Service Running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8002, reload=True)