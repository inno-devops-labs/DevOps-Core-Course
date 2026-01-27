import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import DEBUG, PORT, HOST
from health_check.router import router
from logger_config import setup_logger

setup_logger()
app = FastAPI(debug=DEBUG)
app.include_router(router=router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    uvicorn.run(app=app, port=PORT, host=HOST)
