import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Initialize debugpy for remote debugging when running in Docker
if os.getenv("ENABLE_DEBUGPY") == "true":
    import debugpy
    debugpy.listen(("0.0.0.0", 5678))
    print("🐛 Debugpy listening on port 5678. Ready for debugger to attach...")
    # debugpy.wait_for_client()  # Don't wait - let server start and debugger can attach later

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Auth Service Running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8001, reload=True)