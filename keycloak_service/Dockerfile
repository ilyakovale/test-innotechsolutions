FROM python:3.14-alpine3.22
WORKDIR /python-app
ENV PYTHONUNBUFFERED=1

COPY ./keycloak_service/requirements.txt .
RUN pip install --no-cache -r requirements.txt

COPY ./keycloak_service/ ./keycloak_service/

EXPOSE 8080

CMD ["python", "keycloak_service/__main__.py"]