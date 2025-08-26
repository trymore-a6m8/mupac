import asyncio, \
       aiohttp, \
       aiofiles, \
       os, \
       sys

from pathlib import Path

from concurrent.futures import ProcessPoolExecutor

from bs4 import BeautifulSoup


class DownloadPageParsingError(Exception):
    pass


def get_download_url_from_page(page_html: str, server: str) -> str:
    
    soup = BeautifulSoup(page_html, "html.parser")

    for server_ in [server, "security.ubuntu.com/ubuntu"]:
        download_url_a = soup.find("a", href=lambda url: url and server_ in url)
        if download_url_a is not None:
            return download_url_a["href"]

    raise DownloadPageParsingError


async def download(pool_exec: ProcessPoolExecutor, url: str, platform: str, server: str) -> None:

    package_name: str = url.split('/')[-1]
    download_page_url = f"https://packages.ubuntu.com/noble/{platform}/{package_name}/download"

    async with aiohttp.ClientSession() as session:
        async with session.get(download_page_url) as response:
            page_html = await response.text()

        download_url = await asyncio.get_running_loop().run_in_executor(pool_exec, get_download_url_from_page, *(page_html, server))

        file_name = download_url.split('/')[-1]

        async with session.get(download_url) as response:
            async with aiofiles.open(f"./packages/{file_name}", "bw") as file:
                while (chunk := await response.content.read(1024)):
                    await file.write(chunk)

    return None


async def main(platform: str, server: str) -> int:

    target_folder = Path(os.path.dirname(__file__) + "/packages")
    os.makedirs(target_folder, exist_ok=True)
    for file in target_folder.iterdir():
        if file.is_file():
            file.unlink()

    pool_exec = ProcessPoolExecutor()

    pending = set()

    with open("packages_list.txt", "r", encoding="utf-8") as file:
        for line in file.readlines():
            url = line.strip()
            pending.add(asyncio.create_task(download(pool_exec, url, platform, server)))

    while pending:
        done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)

        for task in done:
            if (task_exception := task.exception()) is not None:
                print(f"Package downloading error: {task_exception}")

    pool_exec.shutdown()


if __name__ == "__main__":
    # python download.py amd64 cz.archive.ubuntu.com/ubuntu
    platform, server = sys.argv[1:3]
    code: int = asyncio.run(main(platform, server))
    sys.exit(code)
