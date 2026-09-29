import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum
from apscheduler.schedulers.background import BackgroundScheduler
from controllers.appRouter import appRouter
from cron_jobs.ticket_timeout_worker import run_ticket_timeout_worker
from cron_jobs.notification_fanout_worker import run_notification_fanout_worker

import os

# Initialize the background scheduler only when running locally outside of AWS Lambda
is_lambda = bool(os.getenv("AWS_LAMBDA_FUNCTION_NAME"))
scheduler = None

if not is_lambda:
    scheduler = BackgroundScheduler()
    # Add jobs: run every 60 seconds
    scheduler.add_job(run_ticket_timeout_worker, "interval", seconds=60, id="ticket_timeout")
    scheduler.add_job(run_notification_fanout_worker, "interval", seconds=60, id="notification_fanout")


@asynccontextmanager
async def lifespan(app: FastAPI):
    if scheduler:
        scheduler.start()
        print("🕐 Background scheduler started (ticket timeout + notification fanout every 60s)")
    yield
    if scheduler:
        scheduler.shutdown()
        print("🛑 Background scheduler stopped")


app = FastAPI(lifespan=lifespan)
handler = Mangum(app, lifespan="off")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(appRouter)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
