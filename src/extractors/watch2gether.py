"""
Watch2Gether
"""
import re

import aiohttp
import async_timeout

from bot.type.errors import Errors
from bot.type.exceptions import BasicError


class Watch2Gether:
    """
    Watch2Gether
    """

    def __init__(self, loop=None) -> None:
        self.session = aiohttp.ClientSession(loop=loop)
        self.base_url = "https://www.watch2gether.com/rooms/create"
        self.pattern = re.compile(
            r"<html><body>You are being <a href=\"(.+)\">redirected</a>\."
            r"</body></html>",
            re.IGNORECASE,
        )

    async def create_new_room(self) -> str:
        """
        Create a new Watch2Gether Room
        @return:
        """
        try:
            async with async_timeout.timeout(timeout=5):
                async with self.session.post(
                    url=self.base_url,
                    allow_redirects=False,
                    # this is the important part, because you can extract
                    # the room url from the redirect
                ) as req:
                    response = await req.text()
                    if req.status == 302:
                        # if the status is not 302, the request failed
                        redirect_url = re.match(self.pattern, response).group(1)
                        return redirect_url
        except (aiohttp.ServerTimeoutError, TimeoutError):
            pass

        raise BasicError(Errors.default)

    async def close(self):
        """
        Close ClientSession
        @return:
        """
        await self.session.close()
