import os
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.security import OAuth2AuthorizationCodeBearer
from fastapi_keycloak_middleware import KeycloakConfiguration, setup_keycloak_middleware, get_user, FastApiUser
from sqlalchemy.orm import Session
from jose import jwt

import crud
import models
from database import Base, engine, get_db
from schemas import MessageIn, MessageOut


KC_URL = os.getenv("KC_URL", "http://keycloak:8080")
KC_HOSTNAME = os.getenv("KC_HOSTNAME", "http://localhost:8080")
REALM = os.getenv("KEYCLOAK_REALM", "test")
CLIENT_ID = os.getenv("KEYCLOAK_CLIENT_ID", "fastapi")

keycloak_config = KeycloakConfiguration(
    url=KC_URL,
    realm=REALM,
    client_id=CLIENT_ID,
    verify_audience=False,
)

oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl=f"{KC_HOSTNAME}/realms/{REALM}/protocol/openid-connect/auth",
    tokenUrl=f"{KC_HOSTNAME}/realms/{REALM}/protocol/openid-connect/token",
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

async def require_admin(request: Request, user: FastApiUser = Depends(get_user)):
    if user is None or not user.is_authenticated:
        raise HTTPException(401, "Not authenticated")

    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        raise HTTPException(401, "Missing token")

    claims = jwt.get_unverified_claims(token)
    roles = claims.get("realm_access", {}).get("roles", [])
    if "admin" not in roles:
        raise HTTPException(403, "Admin role required")

    return user

@app.get("/admin", response_model=list[MessageOut])
async def admin_get(
    db: Session = Depends(get_db),
    user: FastApiUser = Depends(require_admin),
    _token: str = Depends(oauth2_scheme),
):
    """Админская ручка: возвращает все сообщения"""
    return crud.get_all_messages(db)
