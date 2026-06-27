"""
Startup script for AI Stylist API server.

On Windows, uvicorn's default loop setup installs ProactorEventLoop which breaks
psycopg3 async connections. We bypass server.run() entirely and call asyncio.run()
directly with loop_factory to guarantee SelectorEventLoop (Python 3.12+).
"""
import asyncio
import selectors
import sys

import uvicorn

if __name__ == "__main__":
    config = uvicorn.Config(
        "ai_stylist.main:app",
        host="0.0.0.0",
        port=8000,
        loop="none",  # don't let uvicorn touch event loop setup
    )
    server = uvicorn.Server(config)

    if sys.platform == "win32":
        # Bypass server.run() to inject our own loop factory
        asyncio.run(
            server.serve(),
            loop_factory=lambda: asyncio.SelectorEventLoop(selectors.SelectSelector()),
        )
    else:
        asyncio.run(server.serve())
