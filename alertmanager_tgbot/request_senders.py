"""Functions for sending requests"""

import asyncio
import json
from textwrap import dedent
import aiohttp
import aiofiles

from project_logging import root_logger


async def send_post_request(url: str, message: dict, ignored_statuses: list = []) -> dict:
    """
    Send POST request
    args:
       url: URL where the request will be sent
       message: request body
       ignored_statuses: response codes thats will be ignored
    """
    async with aiohttp.ClientSession() as session:
        try:
            async with await session.post(url=url, json=message, timeout=600000) as response:
                response_status = response.status
                response_text = await response.text()
                response.close()
                await session.close()

                if response_status != 200 and response_status not in ignored_statuses:
                    root_logger.error(f"""
                                      failed send post request to - {url}; 
                                      status - {response_status}; 
                                      detail - {response_text}
                                      """)
                    raise WrongResponseCode(url, response_status, response_text)

        except asyncio.TimeoutError as err:
            root_logger.exception(f"Post request time out for url - {url}")
            raise RequestTimeout(url) from err

    try:
        response_text = json.loads(response_text)
        return response_text
    except json.decoder.JSONDecodeError as err:
        root_logger.warning(f"Response is not JSON. Returning raw text - {response_text}")
        raise WrongResponseBodyFromat(url, response_text) from err


async def send_get_request(url: str, ignored_statuses: list =[]) -> dict:
    """
    Send GET request
    args:
       url: URL where the request will be sent
       ignored_statuses: response codes thats will be ignored
    """
    async with aiohttp.ClientSession() as session:
        try:
            async with await session.get(url=url, timeout=600000) as response:
                response_status = response.status
                response_text = await response.text()
                response.close()
                await session.close()

                if response_status != 200 and response_status not in ignored_statuses:
                    root_logger.error(f"""
                                        failed send get request to - {url};
                                        status - {response_status};
                                        detail - {response_text}
                                        """)
                    raise WrongResponseCode(url, response_status, response_text)

        except asyncio.TimeoutError as err:
            root_logger.exception(f"Get request time out for url - {url}")
            raise RequestTimeout(url) from err

    try:
        response_text = json.loads(response_text)
        return response_text
    except json.decoder.JSONDecodeError as err:
        root_logger.warning(f"Response is not JSON. Returning raw text - {response_text}")
        raise WrongResponseBodyFromat(url, response_text) from err


async def send_get_image_request(
        url: str,
        output_file_name: str,
        ignored_statuses: list =[],
        authorization_header: dict = None
    ) -> None:
    """
    Send GET request and save response image
    args:
       url: URL where the request will be sent
       ignored_statuses: response codes thats will be ignored
       output_file_name: filename where respose will be stored
    """
    async with aiohttp.ClientSession() as session:
        try:
            async with await session.get(url=url, timeout=600000, headers=authorization_header) as response:
                response_status = response.status
                if response_status != 200 and response_status not in ignored_statuses:
                    root_logger.error(f"""
                                        failed send get request to - {url};
                                        status - {response_status};
                                        """)
                    raise WrongResponseCode(url, response_status, "Image has not details text")

                image_file = await aiofiles.open(output_file_name, mode='wb')
                await image_file.write(await response.read())
                await image_file.close()
                response.close()
                await session.close()

        except asyncio.TimeoutError as err:
            root_logger.exception(f"Get request time out for url - {url}")
            raise RequestTimeout(url) from err


async def send_delete_request(url: str, ignored_statuses: list =[]) -> None:
    """
    Send DELETE request
    args:
       url: URL where the request will be sent
       ignored_statuses: response codes thats will be ignored
    """
    async with aiohttp.ClientSession() as session:
        try:
            async with await session.delete(url=url, timeout=600000) as response:
                response_status = response.status
                response_text = await response.text()
                response.close()
                await session.close()

                if response_status != 200 and response_status not in ignored_statuses:
                    root_logger.error(f"""
                                        failed send delete request to - {url};
                                        status - {response_status};
                                        detail - {response_text}
                                        """)
                    raise WrongResponseCode(url, response_status, response_text)

        except asyncio.TimeoutError as err:
            root_logger.exception(f"Delete request time out for url - {url}")
            raise RequestTimeout(url) from err


# Module Exceptions


class WrongResponseCode(Exception):
    """
    Exception for cases when response status is not ok
    or ignored
    args:
        url: target url
        status: response status
        details: error details
    """
    def __init__(self, url: str, status: str, details: str):
        self.url = url
        self.status = status
        self.details = details
        super().__init__(
            dedent(f"""
                failed send post request to - {self.url}; 
                status - {self.status}; 
                detail - {self.details}
            """)
        )


class RequestTimeout(Exception):
    """
    Exception for cases when response never awaited
    args:
        url: target url
    """
    def __init__(self, url: str):
        self.url = url
        super().__init__(
            dedent(f"""
                Timeout send request to - {self.url} 
            """)
        )


class WrongResponseBodyFromat(Exception):
    """
    Exception for cases when response have not json body
    args:
        url: target url
        response: response text
    """
    def __init__(self, url: str, response: str):
        self.url = url
        self.response = response
        super().__init__(
            dedent(f"""
                Response body is not json
                url - {self.url}
                response - {self.response}
            """)
        )
