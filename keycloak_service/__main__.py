from keycloak import KeycloakOpenID

keycloak_openid = KeycloakOpenID(
    server_url="http://keycloak:8080/auth/",
    client_id="my_client",
    realm_name="my_realm",
    client_secret_key="my_secret"
)

# Получение токена по логину и паролю
token = keycloak_openid.token("username", "password")

# Обмен кода на токены (grant_type='authorization_code')
token = keycloak_openid.token(grant_type='authorization_code', code='received_code', redirect_uri='callback_url')

# Обновление токена
token = keycloak_openid.refresh_token(token['refresh_token'])

# Выход из системы
keycloak_openid.logout(token['refresh_token'])

# Получение информации о пользователе
userinfo = keycloak_openid.userinfo(token['access_token'])