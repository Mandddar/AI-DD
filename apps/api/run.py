"""
Start script for Windows + Python 3.14.
psycopg3 async requires SelectorEventLoop; Python 3.14's default on Windows is ProactorEventLoop.
Using asyncio.run with loop_factory is the non-deprecated way to fix this.
"""
import asyncio
import selectors
import uvicorn


def selector_loop_factory():
    return asyncio.SelectorEventLoop(selectors.SelectSelector())


if __name__ == "__main__":
    config = uvicorn.Config(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        loop="none",  # tell uvicorn not to manage the loop — we control it
    )
    server = uvicorn.Server(config)
    asyncio.run(server.serve(), loop_factory=selector_loop_factory)
