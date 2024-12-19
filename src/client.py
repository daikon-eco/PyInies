from tqdm.asyncio import tqdm
import requests
from time import time
from datetime import datetime
import asyncio
import httpx
import os
from typing import List, Dict
from datetime import datetime
import logging

from .models import *

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logging.getLogger("httpx").setLevel(logging.WARNING)


class IniesClient:
    def __init__(self, login_infos: LoginInfos = None, max_concurrent_tasks: int = 20):
        if not login_infos:
            self.login_infos = self.login()
        else:
            self.login_infos = login_infos
        self.login_infos_last_update = time()
        self.normes = self.get_normes()
        self.indicators, self.phases = self.get_all_indicators_and_phases()
        self.semaphore = asyncio.Semaphore(max_concurrent_tasks)
        self.client = httpx.AsyncClient(timeout=60.0)

    def login(self):
        url = "https://base-inies.fr/ws/Login"
        payload = {"email": os.getenv("API_LOGIN"), "apiKey": os.getenv("API_KEY")}
        headers = {"content-type": "application/json"}
        logging.info(f"Logging in to {url}.")

        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()

        data = response.json()
        return LoginInfos(**data)

    def get_normes(self):
        url = "https://base-inies.fr/ws/Norme"
        headers = {"authorization": f"Bearer {self.login_infos.access_token}"}
        logging.info(f"Fetching normes")

        response = requests.get(url, headers=headers)
        response.raise_for_status()

        normes = {}
        for resp in response.json():
            normes[resp["id"]] = resp["name"]

        return normes

    def get_all_indicators_and_phases(self):
        indicators: Dict[list] = {}
        phases: Dict[list] = {}
        if not self.normes:
            self.normes = self.get_normes()
        logging.info(f"Fetching indicators and phases")
        for norme_id in self.normes.keys():
            indicators[norme_id], phases[norme_id] = (
                self.get_indicators_and_phases_for_norme(norme_id)
            )
        return indicators, phases

    def get_indicators_and_phases_for_norme(self, norme_id: int):
        url = f"https://base-inies.fr/ws/Norme/{norme_id}"
        headers = {"authorization": f"Bearer {self.login_infos.access_token}"}

        response = requests.get(url, headers=headers)
        response.raise_for_status()
        response = response.json()

        return response["indicators"], response["phases"]

    async def refresh_token(self):
        url = "https://base-inies.fr/ws/RefreshToken"
        headers = {"content-type": "application/json"}
        payload = {
            "accessToken": self.login_infos.access_token,
            "refreshToken": self.login_infos.refresh_token,
        }
        logging.info(f"...Refreshing token...")

        response = await self.client.post(url, json=payload, headers=headers)

        response.raise_for_status()
        self.login_infos = LoginInfos(**response.json())
        self.login_infos_last_update = time()
        logging.info("...Token refreshed successfully.")

    async def get_auth_headers(self):
        if not self.login_infos or time() - self.login_infos_last_update > 20 * 60:
            logging.info("Token expired or missing...")
            await self.refresh_token()
        return {"authorization": f"Bearer {self.login_infos.access_token}"}

    async def get_all_epds(self, since_date: datetime = None) -> List[Epd]:
        all_epds_short = await self.get_all_epds_short(since_date)
        logging.info(f"Number of EPDs to retrieve: {len(all_epds_short)}")

        all_epds = []
        tasks = [
            self.async_func_with_retries(
                async_func=self.get_epd, retries=3, epd_id=epd.id
            )
            for epd in all_epds_short
        ]
        for result in tqdm.as_completed(
            tasks,
            desc=f"Processing EPDs",
            unit="epd",
            total=len(all_epds_short),
        ):
            try:
                epd = await result
                all_epds.append(epd)
            except Exception as e:
                logging.error(f"Error fetching EPD: {e}")

        return all_epds

    async def get_all_epds_short(self, since_date: datetime = None) -> List[EpdShort]:
        url = "https://base-inies.fr/ws/Epd"
        headers = await self.get_auth_headers()
        params = {"includeArchived": "false"}
        if since_date:
            params["referenceDateTime"] = since_date.strftime(r"%Y-%m-%d")

        logging.info(f"Fetching all EPDs (short)")

        response = await self.client.get(url, headers=headers, params=params)
        response.raise_for_status()

        return [EpdShort(**epd) for epd in response.json()]

    async def get_epd(self, epd_id: int) -> Epd:
        url = f"https://base-inies.fr/ws/Epd/{epd_id}"
        headers = await self.get_auth_headers()

        response = await self.client.get(url, headers=headers)
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            logging.error(f"HTTP error: {e.response.status_code} - {e.response.text}")
            raise
        except httpx.RequestError as e:
            logging.error(f"Request error: {e.request.url} - {str(e)}")
            raise

        epd = Epd(**response.json())
        # Populate indicators, phases
        epd.indicatorSet.populate_name(self.normes)
        epd.indicatorSet.populate_indicators(
            self.indicators[epd.indicatorSet.id], self.phases[epd.indicatorSet.id]
        )
        return epd

    async def async_func_with_retries(self, async_func, retries: int, **kwargs):
        for attempt in range(retries):
            async with self.semaphore:
                try:
                    return await async_func(**kwargs)
                except httpx.HTTPStatusError as e:
                    # If it's a 502 or similar transient error, we retry
                    if attempt < retries - 1 and e.response.status_code in [
                        502,
                        503,
                        504,
                    ]:
                        delay = 2**attempt
                        logging.warning(
                            f"HTTP {e.response.status_code} error. Retrying attempt {attempt+2}/{retries} after {delay}s. Args: {kwargs}"
                        )
                        await asyncio.sleep(delay)
                    else:
                        logging.error(
                            f"HTTP error cannot be resolved or no more retries: {e}. Args: {kwargs}"
                        )
                        raise
                except Exception as e:
                    if attempt < retries - 1:
                        delay = 2**attempt
                        logging.warning(
                            f"Error {e}. Retrying attempt {attempt+2}/{retries} after {delay}s. Args: {kwargs}"
                        )
                        await asyncio.sleep(delay)
                    else:
                        logging.error(
                            f"Final attempt failed. Args: {kwargs}, Error: {e}"
                        )
                        raise

    async def close(self):
        await self.client.aclose()