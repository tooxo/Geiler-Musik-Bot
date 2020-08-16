"""
AvAudioSource
"""
import gc
import os
import threading
import time
import traceback
from abc import ABC
from typing import Generator

import av
from discord.oggparse import OggStream
from discord.opus import Encoder as OpusEncoder
from discord.player import AudioSource


class Buffer:
    """
    Interface to interact with os pipes used for buffering.
    """

    def __init__(self) -> None:
        self.read_fd, self.write_fd = os.pipe()
        self.reader = os.fdopen(self.read_fd, "rb")
        self.writer = os.fdopen(self.write_fd, "wb")

        self.available = 0  # bytes available in the buffer
        self.complete = False

    def write(self, data: bytes) -> int:
        """
        Write data to the buffer
        :param data: data
        :return: bytes written
        """
        try:
            if not (self.complete and self.closed):
                if not self.writer.closed:
                    written_bytes = self.writer.write(data)
                    self.available += written_bytes
                    self.writer.flush()
                    return written_bytes
        except (BrokenPipeError, ValueError):
            pass
        return 0

    def read(self, size: int) -> bytes:
        """
        Read bytes from buffer
        :param size: bytes to read
        :return: content
        """
        try:
            if not (self.complete and self.closed):
                while size > self.available:
                    if self.complete:
                        return b""
                    time.sleep(0.001)  # shitty solution FIXME
                if self.__len__() > 0:
                    if size > self.available:
                        self.available = 0
                    else:
                        self.available -= size
                    value = self.reader.read(size)
                    return value
        except BrokenPipeError:
            pass
        return b""

    def flush(self) -> None:
        """
        Empty the buffer
        :return:
        """
        # reads all of the buffer contents without saving
        self.reader.read(self.available)
        self.available = 0

    @property
    def closed(self) -> bool:
        """
        Returns if the buffer is closed
        :return:
        """
        return self.reader.closed or self.writer.closed

    def __del__(self) -> None:
        self.reader.close()
        self.writer.close()

    def __len__(self) -> int:
        return self.available

    @property
    def free(self) -> bool:
        """
        Check if space is free to write to
        :return:
        """
        return self.available < self.halfsize

    @property
    def halfsize(self) -> int:
        """
        Half-Size of buffer object.
        equal to 3 seconds of voice
        :return: maximal size
        """
        # the maximum available size is 64000, but a lower number reduces
        # the response time of volume commands
        # this value is to be determined in the future FIXME?
        return 8000


class AvDecoder:
    """
    Helper class for the AvAudioSource
    """

    # noinspection PyUnresolvedReferences
    def __init__(self, stream: str, volume: float):
        options: dict = dict(
            reconnect_streamed="1",
            reconnect="1",
            reconnect_delay_max="5",
            seekable="1",
            igndts="1",
        )
        self.audio: av.container.InputContainer = av.open(
            stream, "r", timeout=8, options=options
        )

        self.volume = volume

        # pylint: disable=c-extension-no-member
        self.audio_stream: av.audio.stream.AudioStream = (
            self.audio.streams.audio[0]
        )

        self._re_encode: bool = self.audio_stream.codec_context.name != "opus"

        self.output_buffer: Buffer = Buffer()
        self.output_container: av.container.OutputContainer = av.open(
            self.output_buffer, "w", format="opus"
        )

        self.output_stream: av.audio.stream.AudioStream = (
            self.output_container.add_stream("libopus", 48000)
        )

        self.stopped = False

        self.thread = threading.Thread(target=self.fill_buffer)
        self.thread.start()

    def fill_buffer(self) -> None:
        """
        Thread to fill the buffer
        :return: nothing
        """
        packets: Generator[av.Packet, None, None] = self.audio.demux(
            self.audio_stream
        )
        frames: Generator[av.AudioFrame, None, None] = self.audio.decode(
            self.audio_stream
        )
        while not self.stopped:
            while not self.output_buffer.free and not self.stopped:
                time.sleep(0.01)
            # if the volume needs to be changed or the original codec
            # isn't opus, we need to re-encode the sound stream into
            # opus
            if self.volume != 1 or self._re_encode:
                try:
                    frame = next(frames)
                except (StopIteration, av.error.ExitError):
                    break
                frame.pts = None

                if self.volume == 1:
                    # this prevents a new frame from getting created
                    # when the volume is not changed
                    # should use less resources
                    for packet in self.output_stream.encode(frame):
                        self.output_container.mux(packet)
                    continue

                # creates a copy of the audio data and multiplies it by
                # the selected volume
                # noinspection PyArgumentList
                new_frame: av.AudioFrame = av.AudioFrame.from_ndarray(
                    array=frame.to_ndarray() * self.volume,
                    format=frame.format.name,
                    layout=frame.layout.name,
                )
                # reapply "lost" rate
                new_frame.rate = frame.rate

                for packet in self.output_stream.encode(new_frame):
                    self.output_container.mux(packet)
            # if it is already encoded as it is, we can simply copy
            # the stream to output
            else:
                try:
                    packet = next(packets)
                except (StopIteration, av.error.ExitError):
                    break
                packet.pts = None
                packet.dts = None
                # if not packet.pts:
                #     continue
                self.output_container.mux(packet)

        # fix for "1 frames left in the queue on closing"
        # muxes a few dummy frames, until the queue is empty
        for _p in self.output_stream.encode(None):
            self.output_container.mux(_p)

        self.output_buffer.complete = True

        # this should prevent any hard memory leaks
        self.audio.close()
        self.output_buffer.__del__()
        self.output_container.close()
        gc.collect()

    def seek(self, seconds: int) -> None:
        """
        Seeks the audio stream to second n
        :param seconds: n
        :return:
        """
        time_base: int = round(seconds / self.audio_stream.time_base)

        if time_base < 0:
            time_base = max(time_base, -2147483648)
        if time_base > 0:
            time_base = min(time_base, 2147483647)

        # noinspection PyBroadException
        try:
            self.audio.seek(offset=time_base, stream=self.audio_stream)
            self.output_buffer.flush()
        except BaseException:
            # exception probably not needed, because seek either works
            # or ends in a segv
            traceback.print_exc()

    def cleanup(self) -> None:
        """
        Closes all the streams
        :return:
        """
        # asks all streams politely to close
        self.stopped = True


class AvAudioSource(AudioSource, ABC):
    """
    AudioSource for PyAV Bindings
    """

    # noinspection PyUnusedLocal
    def __init__(self, source: str, volume: float, ) -> None:
        """
        Wrapper around AvDecoder for discord.py
        :param source: source stream url
        :param volume: volume
        """
        self.source = source
        self.volume = volume

        self.decoder = AvDecoder(self.source, volume)
        self.stream = OggStream(self.decoder.output_buffer)
        self.iter = self.stream.iter_packets()
        self.bytes_read = 0

    def read(self) -> bytes:
        """
        read 20ms of sound into memory
        :return: sound
        """
        self.bytes_read += OpusEncoder.FRAME_SIZE
        chunk = next(self.iter, b"")
        if chunk == b"":
            # dk why this is needed but okay
            return chunk
        return chunk

    def is_opus(self) -> bool:  # pylint: disable=no-self-use
        """Checks if the audio source is already encoded in Opus."""
        return True

    def cleanup(self) -> None:
        """Called when clean-up is needed to be done.

        Useful for clearing buffer data or processes after
        it is done playing audio.
        """
        if hasattr(self, "decoder"):
            self.decoder.cleanup()

    def set_volume(self, volume: float):
        """
        Set the playback volume
        :param volume: value between 0.0 and 2.0
        :return:
        """
        self.volume = volume
        self.decoder.volume = volume

    def seek(self, seconds: int):
        """
        Seeks the audio stream n seconds forward
        :param seconds: n
        :return:
        """

        # get current position as best as possible
        almost_exact_seconds = round(
            self.bytes_read / 200 / OpusEncoder.SAMPLES_PER_FRAME
        )
        second_to_seek_to = almost_exact_seconds + seconds
        if second_to_seek_to < 0:
            second_to_seek_to = 0

        # update the bytes_read
        self.bytes_read = (
                second_to_seek_to * 200 * OpusEncoder.SAMPLES_PER_FRAME
        )

        return self.decoder.seek(second_to_seek_to)
