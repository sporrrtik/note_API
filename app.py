from typing import Annotated
from fastapi import FastAPI, Depends, Query, Request

from sqlmodel import Session, select
from database import SQLiteDataBase, User, Note
from routers import user, admin
import auth
from logger import logger



db = SQLiteDataBase(db_name="db.db", connect_args={"check_same_thread": False})
SessionDep = Annotated[Session, Depends(db.get_session)]

app = FastAPI()
app.include_router(auth.router)
app.include_router(user.router)
app.include_router(admin.router)

logger.info("Starting API...")


@app.on_event("startup")
def on_startup():
    db.create_db_and_tables()
    db.create_base_users()


@app.middleware("http")
async def log_middleware(request: Request, call_next):
    response = await call_next(request)
    logger.info(f"{request.client.host} {request.method} {request.url} {response.status_code}")
    return response


@app.get("/users/")
def read_users(
        session: SessionDep,
        offset: int = 0,
        limit: Annotated[int, Query(le=100)] = 100,
) -> list[User]:
    users = session.exec(select(User).offset(offset).limit(limit)).all()
    return users
