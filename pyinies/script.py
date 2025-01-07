import asyncio
from datetime import datetime
import logging
import multiprocessing
import os
import sys
from pyinies.process import *
from pyinies.client import IniesClient


# Determine the base path
if getattr(sys, "frozen", False):
    # If the application is run as a bundle, the path is the executable directory
    base_path = os.path.dirname(sys.executable)
else:
    # If run as a script, use the script's directory
    base_path = os.path.dirname(os.path.abspath(__file__))

# Create data and logs directories if they don't exist
data_directory = os.path.join(base_path, "data")
logs_directory = os.path.join(base_path, "logs")
os.makedirs(data_directory, exist_ok=True)
os.makedirs(logs_directory, exist_ok=True)

current_time = datetime.now().strftime("%Y-%m-%d")
log_file = os.path.join(logs_directory, f"{current_time}-logs.txt")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler(log_file), logging.StreamHandler(sys.stdout)],
)
logging.getLogger("httpx").setLevel(logging.WARNING)

_client = None


def get_client():
    global _client
    if _client is None:
        logging.info("Creating IniesClient")
        _client = IniesClient()
    else:
        logging.info("Reusing IniesClient")
    return _client


async def fetch_all_epds():
    client = get_client()
    try:
        return await client.get_all_epds()
    finally:
        await client.close()


async def fetch_epd(epd_id: int):
    client = get_client()
    try:
        return await client.get_epd(epd_id)
    finally:
        await client.close()


def get_epd(epd_id: int):
    epd = asyncio.run(fetch_epd(epd_id))
    return epd


def main():
    multiprocessing.freeze_support()

    logging.info("Starting Zefconnection")
    all_epds = asyncio.run(fetch_all_epds())
    logging.info("Processing EPDs")
    df = process_all_epds(all_epds)
    df = modify_columns_names(df)

    filename = os.path.join(data_directory, f"{current_time}-export_inies.xlsx")

    logging.info(f"Exporting EPDs to {filename}")
    df.to_excel(filename, index=False)
    logging.info("Export completed")


if __name__ == "__main__":
    main()
