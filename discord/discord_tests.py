"""
Runs Instrumentation Tests with distest
"""

import asyncio
import sys
from distest import TestCollector
from distest.interface import TestInterface
from distest import run_dtest_bot
from discord import Embed, Message
from distest.exceptions import ResponseDidNotMatchError


class TestClient:
    def __init__(self):
        self.test_collector = TestCollector()
        self.voice_channel = 598919254359932928
        self.voice_client = None

    def music_manipulation_tests(self):
        @self.test_collector()
        async def __start_music(interface: TestInterface):
            await interface.connect(self.voice_channel)
            await asyncio.sleep(1)
            await interface.assert_reply_equals(
                ",play despacito luis fonsi", "Loading ..."
            )
            await asyncio.sleep(10)
            self.voice_client = interface.voice_client

        @self.test_collector()
        async def test_pause(interface: TestInterface):
            await interface.assert_reply_equals(",pause", "Paused! :pause_button:")
            await asyncio.sleep(1)
            await interface.assert_reply_equals(",pause", "Already Paused.")
            await asyncio.sleep(1)

        @self.test_collector()
        async def test_unpause(interface: TestInterface):
            await interface.assert_reply_equals(",resume", "Unpaused! :play_pause:")
            await asyncio.sleep(1)
            await interface.assert_reply_equals(",resume", "Not Paused.")
            await asyncio.sleep(1)

        @self.test_collector()
        async def test_skip(interface: TestInterface):
            await interface.assert_reply_equals(",skip", "Skipped! :track_next:")
            await asyncio.sleep(1)
            await interface.assert_reply_equals(
                ",skip", "Nothing is playing right now!"
            )
            await asyncio.sleep(1)

        @self.test_collector()
        async def test_pause_b(interface: TestInterface):
            await interface.assert_reply_equals(
                ",pause", "Nothing is playing right now!"
            )
            await asyncio.sleep(1)
            await interface.assert_reply_equals(
                ",unpause", "Nothing is playing right now!"
            )
            await asyncio.sleep(1)

        @self.test_collector()
        async def __clean_up(interface: TestInterface):
            await interface.send_message(",exit")
            await asyncio.sleep(1)
            await self.voice_client.disconnect()
            await asyncio.sleep(5)

    @staticmethod
    def get_last_message_content(interface: TestInterface):
        return interface.channel.last_message().content

    def add_play_tests(self):
        @self.test_collector()
        async def test_play_youtube_url(interface: TestInterface):
            await interface.send_message(content=",play ")  # todo youtube url
            await asyncio.sleep(15)
            if not self.get_last_message_content(interface=interface) == "":
                raise ResponseDidNotMatchError("Message did not match")

    def add_tests(self):
        @self.test_collector()
        async def test_wrong_command(interface):
            """
            Test "Wrong Command"
            :param interface:
            :return:
            """

            embed = Embed(
                title='Command "wrong_command" is not found',
                color=0x00FFCC,
                url="https://github.com/tooxo/Geiler-Musik-Bot/issues",
            )

            await interface.assert_reply_embed_equals(",wrong_command", embed)

        @self.test_collector()
        async def test_nobody_in_channel(interface: TestInterface):
            await interface.assert_reply_equals(",skip", "The bot isn't connected.")

        @self.test_collector()
        async def user_alone_in_channel(interface: TestInterface):
            await interface.connect(self.voice_channel)
            await asyncio.sleep(1)
            await interface.assert_reply_equals(",skip", "The bot isn't connected.")
            await asyncio.sleep(1)
            await interface.disconnect()
            await asyncio.sleep(1)

        @self.test_collector()
        async def test_song_play(interface: TestInterface):
            await interface.connect(self.voice_channel)
            await asyncio.sleep(1)
            try:
                await interface.send_message(",play despacito luis fonsi")
                embed = Embed(title="`Luis Fonsi - Despacito ft. Daddy Yankee`")
                await interface.get_delayed_reply(
                    10, interface.assert_embed_equals, [embed, ["title"]]
                )
            except Exception as e:
                await interface.send_message(",exit")
                await interface.disconnect()
                raise ResponseDidNotMatchError()
            await interface.send_message(",exit")
            await interface.disconnect()

        @self.test_collector()
        async def test_queue_check(interface: TestInterface):
            await asyncio.sleep(3)
            await interface.connect(self.voice_channel)
            await asyncio.sleep(1)
            try:
                await interface.send_message(",play despacito luis fonsi")
                embed = (
                    Embed()
                    .add_field(
                        name="**Currently Playing...**",
                        value="`Luis Fonsi - Despacito ft. Daddy Yankee`",
                    )
                    .add_field(
                        name="**Coming up:**",
                        value="Nothing in Queue. Use .play to add something.",
                    )
                )
                await asyncio.sleep(10)
                await interface.assert_reply_embed_equals(",queue", embed, ["fields"])
            except Exception as e:
                await interface.send_message(",exit")
                await interface.disconnect()
                raise ResponseDidNotMatchError("Response did not match")
            await interface.send_message(",exit")
            await interface.disconnect()

    def start(self):
        self.add_tests()
        self.music_manipulation_tests()
        bot = run_dtest_bot(sys.argv, self.test_collector)


TestClient().start()
