from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    import sys
    return {"message": "AI Service Running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8003, reload=True)