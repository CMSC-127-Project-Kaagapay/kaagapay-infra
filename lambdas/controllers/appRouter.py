from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from controllers.volunteerController import volunteersRouter


appRouter = APIRouter()


@appRouter.get("/", response_class=HTMLResponse)
def welcomeOhara():
    return "<h1>Welcome to Kaagapay API</h1>"


appRouter.include_router(volunteersRouter, tags=["volunteers Routes"])
