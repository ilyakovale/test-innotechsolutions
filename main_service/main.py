import os
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2AuthorizationCodeBearer
from fastapi_keycloak_middleware import (
    KeycloakConfiguration,
    setup_keycloak_middleware,
    get_user,
    FastApiUser,
)

KC_URL = os.getenv("KC_URL", "http://keycloak:8080")
ITERNAL_KC_URL = os.getenv("ITERNAL_KC_URL", "http://localhost:8080")
REALM = os.getenv("KEYCLOAK_REALM", "test")
CLIENT_ID = os.getenv("KEYCLOAK_CLIENT_ID", "fastapi")

keycloak_config = KeycloakConfiguration(
    url=KC_URL,
    realm=REALM,
    client_id=CLIENT_ID,
    decode_options={
        "verify_signature": True,
        "verify_aud": False,   
        "verify_exp": True,
    },
)

oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl=f"{ITERNAL_KC_URL}/realms/{REALM}/protocol/openid-connect/auth",
    tokenUrl=f"{ITERNAL_KC_URL}/realms/{REALM}/protocol/openid-connect/token",
    scopes={"openid": "openid", "profile": "profile", "email": "email"},
)

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


@app.get("/public")
async def public():
    return {"status": "ok"}


@app.get("/authorize")
async def authorize(
    user: FastApiUser = Depends(get_user),
    _token: str = Depends(oauth2_scheme),
):
    if user is None:
        raise HTTPException(401, "Not authenticated")
    return {
        "type": str(type(user)),
        "attributes": dir(user),
        "dict": getattr(user, "__dict__", None),
    }


@app.get("/admin")
async def admin(
    user: FastApiUser = Depends(get_user),
    _token: str = Depends(oauth2_scheme),
):
    if user is None:
        raise HTTPException(401, "Not authenticated")
    return {"status": "ok", "username": user.username}