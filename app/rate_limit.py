import time

requests = {}

MAX_REQUESTS = 60
TIME_WINDOW = 60


def check_rate_limit(client_ip: str):
    current_time = time.time()

    if client_ip not in requests:
        requests[client_ip] = []

    requests[client_ip] = [
        request_time
        for request_time in requests[client_ip]
        if current_time - request_time < TIME_WINDOW
    ]

    if len(requests[client_ip]) >= MAX_REQUESTS:
        return False

    requests[client_ip].append(current_time)

    return True