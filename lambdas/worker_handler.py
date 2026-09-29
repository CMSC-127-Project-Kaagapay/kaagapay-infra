import logging
from cron_jobs.ticket_timeout_worker import run_ticket_timeout_worker
from cron_jobs.notification_fanout_worker import run_notification_fanout_worker

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event, context):
    """
    AWS Lambda handler invoked by Amazon EventBridge scheduled rule (every 1-5 minutes).
    Runs ticket timeout checks and notification fanout tasks.
    """
    logger.info("Starting scheduled background worker execution...")

    try:
        logger.info("Running ticket timeout worker...")
        run_ticket_timeout_worker()
    except Exception as e:
        logger.error(f"Error executing ticket_timeout_worker: {e}", exc_info=True)

    try:
        logger.info("Running notification fanout worker...")
        run_notification_fanout_worker()
    except Exception as e:
        logger.error(f"Error executing notification_fanout_worker: {e}", exc_info=True)

    logger.info("Scheduled background worker execution completed.")
    return {
        "statusCode": 200,
        "body": "Workers executed successfully",
    }


if __name__ == "__main__":
    handler({}, None)
