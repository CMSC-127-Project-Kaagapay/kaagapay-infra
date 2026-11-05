import logging
import uuid

from fastapi import HTTPException, status

logger = logging.getLogger("kaagapay")

GENERIC_MESSAGE = "Something went wrong on our side. Please try again in a moment."


def internal_error(exc: BaseException, context: str = "") -> HTTPException:
    """A 500 that tells the caller nothing about the system.

    The real exception (which can carry the database host, a query or a key) goes to the server log only.
    The caller gets a plain message and a short reference they can quote, which is also in the log line.
    """
    reference = uuid.uuid4().hex[:8]
    logger.error("[%s] %s%s", reference, f"{context}: " if context else "", exc, exc_info=exc)
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"{GENERIC_MESSAGE} (Reference: {reference})",
    )
