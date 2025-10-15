import uvicorn
from fastapi import FastAPI

# Create a minimal FastAPI app
app = FastAPI(title="eShop Test", version="0.1.0")


@app.get("/")
async def root():
    return {"message": "eShop API is running"}


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "version": "0.1.0",
        "timestamp": "2024-01-01T00:00:00Z",
    }


@app.get("/test")
async def test():
    return {"message": "Test endpoint working"}


if __name__ == "__main__":
    print("Starting minimal FastAPI server...")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
