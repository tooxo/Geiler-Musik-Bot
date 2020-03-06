import re

import aiohttp
import async_timeout

from bot.type.errors import Errors
from bot.type.exceptions import BasicError


class Watch2Gether:
    def __init__(self):
        self.session = aiohttp.ClientSession()
        self.base_url = "https://www.watch2gether.com/rooms/create"
        self.pattern = re.compile(
            r"<html><body>You are being <a href=\"(.+)\">redirected</a>\.</body></html>",
            re.IGNORECASE,
        )

    async def create_new_room(self) -> str:
        try:
            async with async_timeout.timeout(timeout=5):
                async with self.session.post(
                    url=self.base_url,
                    # this is not needed as i found out today, you can just do an empty post to create a
                    # new room
                    #
                    # data={
                    #    "utf8": "✓",
                    #    "authenticity_token": "",
                    # },
                    # this is the original data used by watch2gether itself
                    allow_redirects=False,
                    # this is the important part, because you can extract the room url from the redirect
                ) as req:
                    response = await req.text()
                    if req.status == 302:
                        # if the status is not 302, the request failed
                        redirect_url = re.match(self.pattern, response).group(1)
                        return redirect_url
        except (aiohttp.ServerTimeoutError, TimeoutError):
            pass

        raise BasicError(Errors.default)
