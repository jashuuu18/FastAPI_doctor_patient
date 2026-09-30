import time

from fastapi import Request
from fastapi.responses import JSONResponse

from app.rate_limit import check_rate_limit


async def log_response_time(request: Request, call_next):

    client_ip = request.client.host

    if not check_rate_limit(client_ip):
        return JSONResponse(
            status_code=429,
            content={
                "success": False,
                "message": "Too many requests"
            }
        )

    start_time = time.time()

    response = await call_next(request)

    process_time = time.time() - start_time

    print(
        f"{request.method} {request.url.path} "
        f"completed in {process_time:.4f} seconds"
    )

    return response