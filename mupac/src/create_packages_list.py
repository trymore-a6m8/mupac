import asyncio, \
       aiohttp, \
       sys

from bs4 import BeautifulSoup
from pydantic import BaseModel
from concurrent.futures import ProcessPoolExecutor


class PackageDependenciesParsingError(Exception):
    pass


class Package(BaseModel):
    url: str
    required_packages: list[str]


def parse_package_dep(page_html: str) -> list[str]:
    
    dep: list[str] = []
    
    soup = BeautifulSoup(page_html, "html.parser")
    
    try:
        uldep = soup.find_all("ul", class_="uldep")[1]
    except IndexError:
        return []

    for li in uldep.find_all("li"): # type: ignore
        dep.append("https://packages.ubuntu.com" + str(li.find("a")["href"])) # type: ignore

    return dep


async def get_package_data(pool_exec: ProcessPoolExecutor, parent_url: str) -> Package:
    
    async with aiohttp.ClientSession() as session:
        good_response = False

        for _ in range(5):
            async with session.get(parent_url) as response:
                page_html = await response.text()
            
            if response.status == 200:
                good_response = True
                break
            
            await asyncio.sleep(1)

    if not good_response:
        raise PackageDependenciesParsingError

    required_packages: list[str] = await asyncio.get_running_loop().run_in_executor(pool_exec, parse_package_dep, *(page_html,))   # type: ignore

    return Package(
        url=parent_url,
        required_packages=required_packages
    )


async def main(base_url: str) -> int:
    
    pool_exec = ProcessPoolExecutor()

    min_packages_set: set[str] = set()
    pending = {asyncio.create_task(get_package_data(pool_exec, base_url))}
    
    while pending:
        done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)

        for task in done:
            
            if (task_exception := task.exception()) is None:
                package: Package = task.result()
                if package.url not in min_packages_set:
                    min_packages_set.add(package.url)
                    print(package.url)
                
                for child_url in package.required_packages:
                    if child_url not in min_packages_set:
                        pending.add(asyncio.create_task(get_package_data(pool_exec, child_url)))

            else:
                print(f"Package parsing error: {task_exception}")

    with open("packages_list.txt", "bw") as file:
        file.write("\n".join(min_packages_set).encode())

    pool_exec.shutdown()

    return 0


if __name__ == "__main__":
    target = sys.argv[1]
    code: int = asyncio.run(main(target))
    sys.exit(code)

