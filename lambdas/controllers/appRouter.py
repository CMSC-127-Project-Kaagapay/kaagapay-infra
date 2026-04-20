from fastapi import APIRouter, responses
from fastapi.responses import HTMLResponse
# from controllers.authController import authRouter


app_router = APIRouter()


@app_router.get("/", response_class=HTMLResponse)
def welcomeOhara():
    return "<h1>Welcome to Kaagapay API</h1>"


# app_router.include_router(authRouter, tags=["Auth Routes"])
