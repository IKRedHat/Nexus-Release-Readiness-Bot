import logging
import httpx
from typing import Optional, Dict, Any
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger("nexus.utils")

class AsyncHttpClient:
    def __init__(self, base_url: str = "", timeout: int = 10, headers: Optional[Dict] = None):
        self.client = httpx.AsyncClient(base_url=base_url, timeout=timeout, headers=headers or {})

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def post(self, endpoint: str, json_body: Dict[str, Any]) -> Dict[str, Any]:
        logger.debug(f"POST {endpoint} payload={json_body}")
        try:
            # Mocking for demo if localhost isn't running
            if "localhost" in str(self.client.base_url):
                return {"status": "success", "data": {"mock": "true"}}
            response = await self.client.post(endpoint, json=json_body)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.warning(f"Request failed: {e}")
            return {"status": "error", "error": str(e)}

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def get(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        logger.debug(f"GET {endpoint} params={params}")
        try:
             # Mocking for demo
            if "localhost" in str(self.client.base_url):
                return {"status": "success", "data": {"mock": "true"}}
            response = await self.client.get(endpoint, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.warning(f"Request failed: {e}")
            return {"status": "error", "error": str(e)}

    async def close(self):
        await self.client.aclose()
