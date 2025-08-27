import asyncio, \
       argparse

from mupac.src import create_packages_list, download_packages 


def main() -> int:

    parser = argparse.ArgumentParser(
        prog="mupac", 
        description="A tool to download Ubuntu package with minimal required dependencies."
    )

    parser.add_argument("package_url", type=str, help="The URL of the target package (e.g., https://packages.ubuntu.com/noble/amd64/curl).")
    parser.add_argument("platform", type=str, help="The platform (e.g., amd64, i386).")
    parser.add_argument("download_from", type=str, help="The server to download from (e.g., cz.archive.ubuntu.com/ubuntu).")

    args = parser.parse_args()

    code_1: int = asyncio.run(create_packages_list(args.package_url))
    if code_1 != 0:
        print("Failed to create packages list.")
        exit(1)

    code_2: int = asyncio.run(download_packages(args.platform, args.download_from))
    if code_2 != 0:
        print("Failed to download packages.")
        exit(2)

    exit(0)

