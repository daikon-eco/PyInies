import asyncio
from datetime import datetime
import logging
import os
from process import *
from client import IniesClient


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logging.getLogger("httpx").setLevel(logging.WARNING)


async def fetch_all_epds():
    client = IniesClient()
    try:
        return await client.get_all_epds()
    finally:
        await client.close()


async def fetch_epd(epd_id: int):
    client = IniesClient()
    try:
        return await client.get_epd(epd_id)
    finally:
        await client.close()


def get_epd(epd_id: int):
    epd = asyncio.run(fetch_epd(epd_id))
    return epd


def main():
    all_epds = asyncio.run(fetch_all_epds())
    logging.info("Processing EPDs")
    df = process_all_epds(all_epds)
    df = modify_columns_names(df)

    current_time = datetime.now().strftime("%Y-%m-%d")
    # filename = f"./{current_time}-export_inies.xlsx"
    filename = os.path.join(os.getcwd(), "data", f"{current_time}-export_inies.xlsx")

    logging.info(f"Exporting EPDs to {filename}")
    df.to_excel(filename, index=False)


if __name__ == "__main__":
    main()
