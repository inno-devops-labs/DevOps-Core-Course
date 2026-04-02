"""Application entrypoint for local and container execution."""

from src.app import HOST, PORT, app, logger


if __name__ == "__main__":
    logger.info("application_starting", extra={"host": HOST, "port": PORT})
    app.run(host=HOST, port=PORT)
