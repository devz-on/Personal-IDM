import asyncio
import sys
import os
from core.downloader import Downloader


def human_readable(size: int) -> str:
    if size is None or size <= 0:
        return "Unknown"

    size = float(size)
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024

    return f"{size:.2f} PB"


def clear_line():
    sys.stdout.write("\r" + " " * 80 + "\r")


def progress_callback(downloaded: int, total: int):
    clear_line()

    if total <= 0:
        sys.stdout.write(
            f"Downloaded: {human_readable(downloaded)}"
        )
    else:
        percent = (downloaded / total) * 100
        sys.stdout.write(
            f"Downloaded: {human_readable(downloaded)} / "
            f"{human_readable(total)} ({percent:.2f}%)"
        )

    sys.stdout.flush()


async def run():
    if len(sys.argv) < 3:
        print("Usage:")
        print("  python main.py <URL> <output_file>")
        sys.exit(1)

    url = sys.argv[1]
    output = sys.argv[2]

    os.makedirs(os.path.dirname(output) or ".", exist_ok=True)

    downloader = Downloader(
        url=url,
        output_path=output,
        connections=8,
        progress_callback=progress_callback,
        max_speed=10000 * 1024  # 1 MB/s
    )

    try:
        print("Starting download...")
        await downloader.start()
        clear_line()
        print("Download completed successfully ✔")
    except KeyboardInterrupt:
        downloader.stop()
        clear_line()
        print("Download paused ⏸ (resume by running again)")
    except Exception as e:
        clear_line()
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(run())
