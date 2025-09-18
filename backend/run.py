import asyncio
import logging
import uvicorn
from main import app

async def start_server():
    config = uvicorn.Config(app, port=8000, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(start_server())