import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum
from apscheduler.schedulers.background import BackgroundScheduler
from controllers.appRouter import appRouter
from cron_jobs.ticket_timeout_worker import run_ticket_timeout_worker
from cron_jobs.notification_fanout_worker import run_notification_fanout_worker

# Initialize the background scheduler
scheduler = BackgroundScheduler()

# Add jobs: run every 60 seconds
scheduler.add_job(run_ticket_timeout_worker, "interval", seconds=60, id="ticket_timeout")
scheduler.add_job(run_notification_fanout_worker, "interval", seconds=60, id="notification_fanout")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: start the scheduler
    scheduler.start()
    print("🕐 Background scheduler started (ticket timeout + notification fanout every 60s)")
    yield
    # Shutdown: stop the scheduler
    scheduler.shutdown()
    print("🛑 Background scheduler stopped")


app = FastAPI(lifespan=lifespan)
handler = Mangum(app, lifespan="off")


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(appRouter)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
