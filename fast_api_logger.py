import logging

from fastapi import Request


async def log_request(request: Request):
    """Function for logging incoming requests"""
    logging.info("Request: %s - %s", request.method, request.url)
    logging.info("Request headers: %s", request.headers)
    logging.info("Request content: %s", await request.body())


def log_response(response):
    """Function for logging responses (JSON serializable python objects)."""
    logging.info("Response: %s", response)
    return response
