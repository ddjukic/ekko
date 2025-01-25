import time

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pyngrok import ngrok

app = FastAPI()
security = HTTPBearer()


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    correct_token = "test_token"  # Replace this with your token
    if credentials.credentials != correct_token:
        raise HTTPException(status_code=403, detail="Invalid authentication token")
    return credentials.credentials


@app.get("/stream")
async def stream_data(token: str = Depends(verify_token)):
    def event_stream():
        # For demonstration, let's just count to 10 at 1-second intervals.
        # Replace this with your actual logic to stream data.
        for i in range(1, 11):
            yield f"data: {i}\n\n"
            time.sleep(1)

    return StreamingResponse(event_stream(), media_type="text/event-stream")


if __name__ == "__main__":
    # Tunnel the FastAPI server on port 8000
    public_url = ngrok.connect(8000)
    print(f"Public URL: {public_url}")
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
