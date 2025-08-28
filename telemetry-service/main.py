from fastapi import FastAPI
import os

if os.getenv("ENABLE_DEBUGPY") == "true":
    import debugpy
    debugpy.listen(("0.0.0.0", 5679))
    print("🐛 Debugpy listening on port 5679. Waiting for debugger to attach...")
    # debugpy.wait_for_client()

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Telemetry Service Running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8002, reload=True)