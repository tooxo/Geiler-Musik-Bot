"""
Runs Instrumentation Tests with distest
"""

import asyncio
import sys
from distest import TestCollector
from distest.interface import TestInterface
from distest import run_dtest_bot
from discord import Embed
from distest.exceptions import ResponseDidNotMatchError

test_collector = TestCollector()


@test_collector()
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


@test_collector()
async def test_song_play(interface: TestInterface):
    await interface.connect(598919254359932928)
    await asyncio.sleep(1)
    try:
        await interface.send_message(",play despacito luis fonsi")
        embed = Embed(title="`Luis Fonsi - Despacito ft. Daddy Yankee`")
        await interface.get_delayed_reply(
            5, interface.assert_embed_equals, [embed, ["title"]]
        )
    except Exception as e:
        await interface.send_message(",exit")
        await interface.disconnect()
        raise ResponseDidNotMatchError()
    await interface.send_message(",exit")
    await interface.disconnect()


@test_collector()
async def test_queue_check(interface: TestInterface):
    await asyncio.sleep(3)
    await interface.connect(598919254359932928)
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
        await asyncio.sleep(5)
        await interface.assert_reply_embed_equals(",queue", embed, ["fields"])
    except Exception as e:
        await interface.send_message(",exit")
        await interface.disconnect()
        raise ResponseDidNotMatchError
    await interface.send_message(",exit")
    await interface.disconnect()


@test_collector()
async def test_send(interface):
    await interface.send_message(".Test")


if __name__ == "__main__":
    bot = run_dtest_bot(sys.argv, test_collector)
