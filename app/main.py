from uvicorn import run

from starlette.requests import Request
from fastapi import FastAPI

from app import settings
from app.routers.v1 import router as api_router
from app.connects.postgres.session import Session, engine
from app.connects.postgres.base import DBBase

DBBase.metadata.create_all(bind=engine)

def get_application() -> FastAPI:
    application = FastAPI(
        title=settings.PROJECT_NAME, debug=settings.DEBUG,
        version=settings.VERSION
    )
    application.include_router(
        api_router, prefix=settings.API_PREFIX,
    )
    return application


app = get_application()

@app.middleware("http")
async def db_session_middleware(request: Request, call_next):

    request.state.db = Session()
    response = await call_next(request)
    request.state.db.close()

    return response
# debug only
if __name__ == "__main__":
    run(app, host="0.0.0.0", port=8000)
