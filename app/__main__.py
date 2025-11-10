from app.main import app
import os

# Load host and port from environment variables
host = os.getenv("APP_HOST")
port = int(os.getenv("APP_PORT"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=host, port=port, reload=True)