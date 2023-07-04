import uvicorn
from fastapi import FastAPI
from wg_api.routers import running_router, configs_router


app = FastAPI()
app.include_router(running_router)
app.include_router(configs_router)


if __name__ == "__main__":
    uvicorn.run("main:app", reload=True, port=5000, host='0.0.0.0', log_level="debug")
