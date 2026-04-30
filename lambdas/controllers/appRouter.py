from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from controllers.volunteerController import volunteersRouter
from controllers.incidentTicketController import router as incidentTicketsRouter
from controllers.adminController import router as adminRouter
from controllers.alliedOfficeController import router as alliedOfficeRouter


appRouter = APIRouter()


@appRouter.get("/", response_class=HTMLResponse)
def welcomeOhara():
    return "<h1>Welcome to Kaagapay API</h1>"


appRouter.include_router(volunteersRouter, tags=["volunteers Routes"])
appRouter.include_router(incidentTicketsRouter, tags=["Incident Tickets Routes"])
appRouter.include_router(adminRouter, tags=["Admin Routes"])
appRouter.include_router(alliedOfficeRouter, tags=["Allied Office Routes"])
