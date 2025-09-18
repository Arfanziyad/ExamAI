import multiprocessing
import uvicorn
import logging.config
from logging_config import LOGGING_CONFIG
import os

def run_server(host="127.0.0.1", port=8000):
    # Configure logging
    logging.config.dictConfig(LOGGING_CONFIG)
    logger = logging.getLogger(__name__)
    logger.info("Starting server with enhanced logging configuration")
    
    config = uvicorn.Config(
        "main:app",
        host=host,
        port=port,
        log_level="debug",
        loop="asyncio",
        workers=1,
        reload=True
    )
    
    server = uvicorn.Server(config)
    server.run()

if __name__ == "__main__":
    # Ensure the storage directories exist
    storage_dirs = [
        "storage/uploads",
        "storage/processed",
        "storage/model_answers",
        "storage/question_papers",
        "storage/submissions",
    ]
    for directory in storage_dirs:
        os.makedirs(directory, exist_ok=True)

    # Configure logging
    logging.config.dictConfig(LOGGING_CONFIG)
    logger = logging.getLogger(__name__)
    logger.info("Starting server with enhanced logging configuration")
    
    # Configure uvicorn with error handling
    try:
        config = uvicorn.Config(
            "main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,      # Enable auto-reload for development
            workers=1,        # Use single worker for debugging
            log_level="info",
            log_config=LOGGING_CONFIG,
            access_log=True,
            timeout_keep_alive=65,    # Increase keep-alive timeout
            limit_max_requests=0,     # No request limit
            lifespan="on"            # Enable lifespan events
        )
        
        server = uvicorn.Server(config)
        logger.info("Server configuration complete, starting server...")
        server.run()
        
    except Exception as e:
        logger.error(f"Failed to start server: {str(e)}")
        raise