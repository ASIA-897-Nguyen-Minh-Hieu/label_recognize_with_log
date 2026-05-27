import base64
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from lambda_function import lambda_handler
import uvicorn

app = FastAPI(title="Label Recognize Local Server")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/label-recognize")
async def label_recognize(request: Request):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")
        
    # The lambda function expects event['body-json']
    event = {
        "body-json": body
    }
    
    # Run the lambda handler
    try:
        response = lambda_handler(event, None)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/stag/label-recognize")
async def label_recognize_stag(request: Request):
    return await label_recognize(request)

@app.get("/")
def index():
    return {"message": "Label Recognize Local Server is running!"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
