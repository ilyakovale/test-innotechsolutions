import os
import sys
import time
import httpx
from keycloak import KeycloakAdmin
from keycloak.exceptions import KeycloakGetError

# --- Конфигурация из env ---
KEYCLOAK_URL = os.getenv("KEYCLOAK_URL", "http://keycloak:8080")
KEYCLOAK_PUBLIC_URL = os.getenv("KEYCLOAK_PUBLIC_URL", "http://localhost:8080")
REALM = os.getenv("KEYCLOAK_REALM", "test")
ADMIN_USER = os.getenv("KC_BOOTSTRAP_ADMIN_USERNAME")
ADMIN_PASS = os.getenv("KC_BOOTSTRAP_ADMIN_PASSWORD")

CLIENT_ID = os.getenv("KEYCLOAK_CLIENT_ID", "fastapi")
FASTAPI_URL = os.getenv("FASTAPI_PUBLIC_URL", "http://localhost:8000")

SMTP_CONFIG = {
    "host": os.getenv("SMTP_HOST"),
    "port": os.getenv("SMTP_PORT"),
    "from": os.getenv("SMTP_FROM"),
    "user": os.getenv("SMTP_USER"),
    "password": os.getenv("SMTP_PASSWORD"),
    "starttls": "true",
    "auth": "true",
}


def wait_for_keycloak():
    for _ in range(60):
        try:
            r = httpx.get(f"{KEYCLOAK_URL}/realms/master", timeout=2)
            if r.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(2)
    return False


def get_admin():
    return KeycloakAdmin(
        server_url=KEYCLOAK_URL,
        username=ADMIN_USER,
        password=ADMIN_PASS,
        realm_name=REALM,          # работаем в целевом Realm
        user_realm_name="master",  # логинимся через master
        verify=True,
    )


def setup_realm(admin):
    """Настройки Realm: verify email, регистрация, вход по email."""
    payload = {
        "verifyEmail": True,
        "registrationAllowed": True,
        "loginWithEmailAllowed": True,
        "duplicateEmailsAllowed": False,
        "resetPasswordAllowed": True,
        "editUsernameAllowed": False,
        "accessTokenLifespan": 900,
        "smtpServer": SMTP_CONFIG,
    }
    admin.update_realm(realm_name=REALM, payload=payload)
    print(f"✓ Realm '{REALM}' обновлён (verifyEmail, registration, SMTP)")


def setup_client(admin):
    """Создаём или обновляем публичный клиент для FastAPI."""
    client_payload = {
        "clientId": CLIENT_ID,
        "name": "FastAPI Swagger",
        "enabled": True,
        "publicClient": True,
        "standardFlowEnabled": True,
        "directAccessGrantsEnabled": False,
        "serviceAccountsEnabled": False,
        "protocol": "openid-connect",
        "redirectUris": [
            f"{FASTAPI_URL}/*",
            f"{FASTAPI_URL}/docs/oauth2-redirect",
        ],
        "webOrigins": [FASTAPI_URL],
        "attributes": {
            "pkce.code.challenge.method": "S256",
            "post.logout.redirect.uris": f"{FASTAPI_URL}/*",
        },
    }

    # Проверяем, существует ли клиент
    existing = admin.get_clients()
    client_uuid = None
    for c in existing:
        if c["clientId"] == CLIENT_ID:
            client_uuid = c["id"]
            break

    if client_uuid:
        admin.update_client(client_id=client_uuid, payload=client_payload)
        print(f"✓ Клиент '{CLIENT_ID}' обновлён")
    else:
        admin.create_client(payload=client_payload, skip_exists=True)
        print(f"✓ Клиент '{CLIENT_ID}' создан")


def main():
    if not wait_for_keycloak():
        print("✗ Keycloak не доступен", file=sys.stderr)
        sys.exit(1)

    try:
        admin = get_admin()
        setup_realm(admin)
        setup_client(admin)
        print("✓ Настройка завершена успешно")
        sys.exit(0)
    except KeycloakGetError as e:
        print(f"✗ Ошибка Keycloak: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"✗ Ошибка: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()