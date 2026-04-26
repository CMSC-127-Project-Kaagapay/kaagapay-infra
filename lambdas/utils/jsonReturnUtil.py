from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder


def jsonResponse(payload, key: str = "data"):
    return JSONResponse(
        content={
            key: jsonable_encoder(payload),
        }
    )
