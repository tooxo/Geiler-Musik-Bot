import random
import re

import aiohttp
import async_timeout

from bot.type.error import Error
from bot.type.errors import Errors


class Watch2Gether:
    def __init__(self):
        self.session = aiohttp.ClientSession()
        self.base_url = "https://www.watch2gether.com/rooms/create"
        self.pattern = re.compile(
            r"<html><body>You are being <a href=\"(.+)\">redirected</a>\.</body></html>",
            re.IGNORECASE,
        )
        # these tokens are extracted from requests created by the site itself in the networking tab of the chrome
        # developer settings
        self.tokens = [
            "YLxjPozp1eSYplEoUMYsMdJfeuk4mBSUDehd9rq27kJ5xsgV3D/bmwehVA+Vr9Sm/0qOVe0IZhoAvoXzqh/eZA==",
            "irRFFH4cSQOMEJgOMo5VPADfHT8fFR6/3IGGVN26EkmTzu4/LspHfBMXnSn3562rLcrpg8qFbDHR115RzRMibw==",
        ]

    async def create_new_room(self) -> (str, Error):
        try:
            async with async_timeout.timeout(timeout=5):
                async with self.session.post(
                    url=self.base_url,
                    data={
                        "utf8": "✓",
                        "authenticity_token": random.choice(self.tokens),
                    },
                    allow_redirects=False,
                ) as req:
                    response = await req.text()

                    if req.status == 302:
                        redirect_url = re.match(self.pattern, response).group(1)
                        return redirect_url
        except (aiohttp.ServerTimeoutError, TimeoutError):
            pass
        return Error(True, Errors.default)
