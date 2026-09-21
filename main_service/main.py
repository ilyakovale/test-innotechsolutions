import os
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2AuthorizationCodeBearer
from fastapi_keycloak_middleware import (
    KeycloakConfiguration,
    setup_keycloak_middleware,
    get_user,
    FastApiUser,
)
from sqlalchemy.orm import Session

import crud
import models
from database import Base, engine, get_db
from schemas import MessageIn, MessageOut


KC_URL = os.getenv("KC_URL", "http://keycloak:8080")
ITERNAL_KC_URL = os.getenv("ITERNAL_KC_URL", "http://localhost:8080")
REALM = os.getenv("KEYCLOAK_REALM", "test")
CLIENT_ID = os.getenv("KEYCLOAK_CLIENT_ID", "fastapi")

keycloak_config = KeycloakConfiguration(
    url=KC_URL,
    realm=REALM,
    client_id=CLIENT_ID,
    verify_audience=False,
)

oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl=f"{ITERNAL_KC_URL}/realms/{REALM}/protocol/openid-connect/auth",
    tokenUrl=f"{ITERNAL_KC_URL}/realms/{REALM}/protocol/openid-connect/token",
    scopes={"openid": "openid", "profile": "profile", "email": "email"},
)


Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="Test API",
    swagger_ui_init_oauth={
        "clientId": CLIENT_ID,
        "usePkceWithAuthorizationCodeGrant": True,
        "scopes": "openid profile email",
    },
)

setup_keycloak_middleware(
    app,
    keycloak_configuration=keycloak_config,
    add_swagger_auth=False,
    exclude_patterns=[
        r"^/docs(/.*)?$",
        r"^/openapi\.json$",
        r"^/redoc(/.*)?$",
        r"^/$",
        r"^/public$",
    ],
)


@app.get("/")
async def root():
    return {"status": "ok"}


@app.post("/public", response_model=MessageOut)
async def public_post(payload: MessageIn, db: Session = Depends(get_db)):
    """Публичная ручка: сообщение в БД без пользователя."""
    return crud.create_message(db, text=payload.text)


@app.post("/authorize", response_model=MessageOut)
async def authorize_post(
    payload: MessageIn,
    db: Session = Depends(get_db),
    user: FastApiUser = Depends(get_user),
    _token: str = Depends(oauth2_scheme),
):
    """Защищённая ручка: сообщение с именем пользователя."""
    if user is None or not user.is_authenticated:
        raise HTTPException(401, "Not authenticated")
    return crud.create_message(
        db,
        text=payload.text,
        username=user.display_name,
        is_authenticated=True,
    )


@app.get("/admin", response_model=list[MessageOut])
async def admin_get(
    db: Session = Depends(get_db),
    user: FastApiUser = Depends(get_user),
    _token: str = Depends(oauth2_scheme),
):
    """Админская ручка: возвращает все сообщения"""
    if user is None or not user.is_authenticated:
        raise HTTPException(401, "Not authenticated")
    return crud.get_all_messages(db)