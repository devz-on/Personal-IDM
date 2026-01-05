import asyncio
import aiohttp
import ssl
from typing import Callable, Optional
from dataclasses import dataclass

from core.speed_limiter import SpeedLimiter


CHUNK_READ = 64 * 1024  # 64 KB read buffer


class DownloadCancelled(Exception):
    pass


@dataclass
class Segment:
    start: int
    end: int
    downloaded: int = 0


class Downloader:
    """
    Classic IDM-style downloader:
    - File split into EXACTLY N segments
    - Each stream downloads ONE continuous segment
    """

    def __init__(
        self,
        url: str,
        output_path: str,
        connections: int = 8,
        progress_callback: Optional[Callable] = None,
        stream_callback: Optional[Callable] = None,
        verify_ssl: bool = False,
        max_speed: int = 0,
    ):
        self.url = url
        self.output_path = output_path
        self.connections = connections
        self.progress_callback = progress_callback
        self.stream_callback = stream_callback
        self._stop = False

        self._file_size = 0
        self._downloaded = 0
        self.segments: list[Segment] = []

        self.limiter = SpeedLimiter(max_speed)

        if not verify_ssl:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            self.ssl_context = ctx
        else:
            self.ssl_context = None

    # ---------------- PUBLIC ----------------

    def stop(self):
        self._stop = True

    async def start(self):
        try:
            await self._segmented_download()
        except Exception:
            await self._single_download()

    # ---------------- SEGMENTED MODE ----------------

    async def _segmented_download(self):
        timeout = aiohttp.ClientTimeout(total=None)
        connector = aiohttp.TCPConnector(ssl=self.ssl_context)

        async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
            async with session.head(self.url) as r:
                if r.status >= 400:
                    raise Exception("HEAD failed")

                self._file_size = int(r.headers.get("Content-Length", 0))

            if self._file_size <= 0:
                raise Exception("No Content-Length")

            # prepare file
            with open(self.output_path, "wb") as f:
                f.truncate(self._file_size)

            self._create_segments()
            self._downloaded = 0

            tasks = [
                asyncio.create_task(self._download_segment(session, i, seg))
                for i, seg in enumerate(self.segments)
            ]

            await asyncio.gather(*tasks)

    def _create_segments(self):
        """Split file into EXACTLY N equal segments"""
        self.segments.clear()
        part = self._file_size // self.connections

        for i in range(self.connections):
            start = i * part
            end = (
                self._file_size - 1
                if i == self.connections - 1
                else start + part - 1
            )
            self.segments.append(Segment(start, end))

    async def _download_segment(self, session, stream_id: int, seg: Segment):
        start = seg.start
        end = seg.end

        headers = {"Range": f"bytes={start}-{end}"}

        async with session.get(self.url, headers=headers) as r:
            if r.status not in (200, 206):
                raise Exception("Range not supported")

            pos = start
            with open(self.output_path, "r+b") as f:
                f.seek(start)

                async for chunk in r.content.iter_chunked(CHUNK_READ):
                    if self._stop:
                        raise DownloadCancelled()

                    f.write(chunk)
                    size = len(chunk)

                    pos += size
                    seg.downloaded += size
                    self._downloaded += size

                    await self.limiter.throttle(size)

                    if self.stream_callback:
                        self.stream_callback(
                            stream_id,
                            seg.downloaded,
                            seg.start,
                            seg.end,
                        )

                    if self.progress_callback:
                        self.progress_callback(
                            self._downloaded,
                            self._file_size,
                        )

    # ---------------- SINGLE STREAM FALLBACK ----------------

    async def _single_download(self):
        timeout = aiohttp.ClientTimeout(total=None)
        connector = aiohttp.TCPConnector(ssl=self.ssl_context)

        async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
            async with session.get(self.url) as r:
                if r.status >= 400:
                    raise Exception("Download failed")

                total = int(r.headers.get("Content-Length", 0))
                self._file_size = total

                with open(self.output_path, "wb") as f:
                    async for chunk in r.content.iter_chunked(CHUNK_READ):
                        if self._stop:
                            raise DownloadCancelled()

                        f.write(chunk)
                        size = len(chunk)
                        self._downloaded += size

                        await self.limiter.throttle(size)

                        if self.stream_callback:
                            self.stream_callback(0, self._downloaded, 0, total)

                        if self.progress_callback:
                            self.progress_callback(self._downloaded, total)
