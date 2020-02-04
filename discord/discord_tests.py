"""
Runs Instrumentation Tests with distest
"""

import asyncio
import sys

from distest import TestCollector, run_dtest_bot
from distest.exceptions import ResponseDidNotMatchError
from distest.interface import TestInterface

from discord import Embed, Message


class TestClient:
    def __init__(self):
        self.test_collector = TestCollector()
        self.voice_channel = 598919254359932928
        self.voice_client = None

    def music_manipulation_tests(self):
        @self.test_collector()
        async def __start_music(interface: TestInterface):
            self.voice_client = await interface.connect(self.voice_channel)
            await asyncio.sleep(1)
            await interface.assert_reply_equals(
                ",play despacito luis fonsi", "Loading ..."
            )
            await asyncio.sleep(10)

        @self.test_collector()
        async def test_pause(interface: TestInterface):
            await interface.assert_reply_equals(
                ",pause", "Paused! :pause_button:"
            )
            await asyncio.sleep(1)
            await interface.assert_reply_equals(",pause", "Already Paused.")
            await asyncio.sleep(1)

        @self.test_collector()
        async def test_unpause(interface: TestInterface):
            await interface.assert_reply_equals(
                ",resume", "Unpaused! :play_pause:"
            )
            await asyncio.sleep(1)
            await interface.assert_reply_equals(",resume", "Not Paused.")
            await asyncio.sleep(1)

        @self.test_collector()
        async def test_skip(interface: TestInterface):
            await interface.assert_reply_equals(
                ",skip", "Skipped! :track_next:"
            )
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
            await interface.assert_reply_equals(
                ",skip", "The bot isn't connected."
            )

        @self.test_collector()
        async def user_alone_in_channel(interface: TestInterface):
            await interface.connect(self.voice_channel)
            await asyncio.sleep(1)
            await interface.assert_reply_equals(
                ",skip", "The bot isn't connected."
            )
            await asyncio.sleep(1)
            await interface.disconnect()
            await asyncio.sleep(1)

        @self.test_collector()
        async def test_song_play(interface: TestInterface):
            await interface.connect(self.voice_channel)
            await asyncio.sleep(1)

            await interface.send_message(",play despacito luis fonsi")
            await asyncio.sleep(10)
            await interface.assert_message_equals(
                await interface.get_last_message(),
                "`Luis Fonsi - Despacito ft. Daddy Yankee`",
            )
            await asyncio.sleep(2)
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
                await interface.assert_reply_embed_equals(
                    ",queue", embed, ["fields"]
                )
            except Exception as e:
                await interface.send_message(",exit")
                await interface.disconnect()
                raise ResponseDidNotMatchError("Response did not match")
            await interface.send_message(",exit")
            await interface.disconnect()

    def extractor_tests(self):
        @self.test_collector()
        async def youtube_url(interface: TestInterface):
            youtube_url = "https://www.youtube.com/watch?v=q0hyYWKXF0Q"
            await interface.connect(self.voice_channel)
            await interface.send_message(content=",p " + youtube_url)
            await asyncio.sleep(10)
            last_message = await interface.get_last_message()
            await interface.assert_message_equals(
                message=last_message, matches="`TONES AND I - DANCE MONKEY`"
            )
            await interface.send_message(",exit")
            await interface.disconnect()
            await asyncio.sleep(2)

        @self.test_collector()
        async def youtube_term(interface: TestInterface):
            youtube_term = "tones & i dance monkey"
            await interface.connect(self.voice_channel)
            await interface.send_message(content=",p " + youtube_term)
            await asyncio.sleep(10)
            last_message = await interface.get_last_message()
            await interface.assert_message_equals(
                message=last_message, matches="`TONES AND I - DANCE MONKEY`"
            )
            await interface.send_message(",exit")
            await interface.disconnect()
            await asyncio.sleep(3)

        @self.test_collector()
        async def spotify_track(interface: TestInterface):
            spotify_url = "https://open.spotify.com/track/5ZULALImTm80tzUbYQYM9d?si=qP8FvIhZSHGcIGGSe4OP3g"
            await interface.connect(self.voice_channel)
            await interface.send_message(content=",p " + spotify_url)
            await asyncio.sleep(10)
            last_message = await interface.get_last_message()
            await interface.assert_message_equals(
                message=last_message, matches="`TONES AND I - DANCE MONKEY`"
            )
            await interface.send_message(",exit")
            await interface.disconnect()
            await asyncio.sleep(2)

        @self.test_collector()
        async def spotify_playlist(interface: TestInterface):
            spotify_url = "https://open.spotify.com/playlist/37i9dQZEVXbMDoHDwVN2tF?si=ZphJKc-3T-Ov6zeXGi9lnw"
            await interface.connect(self.voice_channel)
            await interface.assert_reply_equals(
                ",p " + spotify_url,
                ":asterisk: Added 50 Tracks to Queue. :asterisk:",
            )
            # top 50 so its 50 songs every time
            await asyncio.sleep(3)
            await interface.send_message(",exit")
            await interface.disconnect()
            await asyncio.sleep(2)

        @self.test_collector()
        async def spotify_artist(interface: TestInterface):
            spotify_url = "https://open.spotify.com/artist/5K4W6rqBFWDnAN6FQUkS6x?si=YWvqun8PTWmqSPfs7YKtqw"
            await interface.connect(self.voice_channel)
            await interface.assert_reply_equals(
                ",p " + spotify_url,
                ":asterisk: Added 10 Tracks to Queue. :asterisk:",
            )
            # top 10 so its 10 songs every time
            await asyncio.sleep(3)
            await interface.send_message(",exit")
            await interface.disconnect()
            await asyncio.sleep(2)

        @self.test_collector()
        async def spotify_album(interface: TestInterface):
            spotify_url = "https://open.spotify.com/album/1A3nVEWRJ8yvlPzawHI1pQ?si=DyQA_PVrQzOAHKrcpoP9ww"
            await interface.connect(self.voice_channel)
            await interface.assert_reply_equals(
                ",p " + spotify_url,
                ":asterisk: Added 18 Tracks to Queue. :asterisk:",
            )
            await asyncio.sleep(3)
            await interface.send_message(",exit")
            await interface.disconnect()
            await asyncio.sleep(2)

        @self.test_collector()
        async def youtube_playlist(interface: TestInterface):
            spotify_url = "https://www.youtube.com/playlist?list=PLw-VjHDlEOgtl4ldJJ8Arb2WeSlAyBkJS"
            await interface.connect(self.voice_channel)
            await interface.assert_reply_equals(
                ",p " + spotify_url,
                ":asterisk: Added 100 Tracks to Queue. :asterisk:",
            )
            # top 100 so its 100 songs every time
            await asyncio.sleep(3)
            await interface.send_message(",exit")
            await interface.disconnect()
            await asyncio.sleep(2)

        @self.test_collector()
        async def queue(interface: TestInterface):
            await interface.connect(self.voice_channel)
            await interface.send_message(",p tones & i dance monkey")
            await asyncio.sleep(3)
            await interface.assert_reply_equals(
                ",p kanye west follow god",
                ":asterisk: Added **kanye west follow god** to Queue.",
            )
            await asyncio.sleep(2)
            await interface.send_message(",s")
            await asyncio.sleep(5)
            last_message = await interface.get_last_message()
            await interface.assert_message_equals(
                last_message, "`Kanye West - Follow God`"
            )
            await asyncio.sleep(1)
            await interface.send_message(",exit")
            await interface.disconnect()

    def queue_tests(self):
        @self.test_collector()
        async def queue_empty(interface: TestInterface):
            await interface.assert_reply_equals(
                ",queue",
                "**Currently Playing ...**\nNothing.\n**Coming up:**\n"
                "Nothing in Queue. Use .play to add something.",
            )

        @self.test_collector()
        async def queue_full(interface: TestInterface):
            await interface.connect(self.voice_channel)
            await interface.send_message(
                ",p https://www.youtube.com/playlist?list=PLw-VjHDlEOgtl4ldJJ8Arb2WeSlAyBkJS"
            )
            await asyncio.sleep(3)
            await interface.assert_reply_contains(",q", "`(+)` `90 Tracks...`")
            await asyncio.sleep(2)
            await interface.send_message(",exit")
            await asyncio.sleep(2)
            await interface.disconnect()

    def shuffle_test(self):
        @self.test_collector()
        async def test_shuffle_full(interface: TestInterface):
            await interface.connect(self.voice_channel)
            await interface.send_message(",p charts")
            await asyncio.sleep(3)
            await interface.send_message(",q")
            message = await interface.get_last_message()
            await asyncio.sleep(2)
            await interface.assert_reply_equals(
                ",shuffle", "Shuffled! :twisted_rightwards_arrows:"
            )
            await asyncio.sleep(1)
            await interface.send_message(",q")
            await asyncio.sleep(1)
            message2 = await interface.get_last_message()
            if message.content == message2.content:
                raise ResponseDidNotMatchError
            await interface.send_message(",exit")
            await asyncio.sleep(1)
            await interface.disconnect()
            await asyncio.sleep(2)

        @self.test_collector()
        async def test_shuffle_empty(interface: TestInterface):
            await interface.connect(self.voice_channel)
            await interface.send_message(",p luis fonsi despacito")
            await asyncio.sleep(2)
            await interface.assert_reply_equals(
                ",shuffle", "The queue is empty. :cloud:"
            )
            await interface.send_message(",exit")
            await interface.disconnect()

    def start(self):
        self.add_tests()
        self.music_manipulation_tests()
        self.extractor_tests()
        self.queue_tests()
        self.shuffle_test()
        bot = run_dtest_bot(sys.argv, self.test_collector)


TestClient().start()
