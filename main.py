import asyncio
import aiohttp


URLS = [
    "https://httpbin.org/get",
    "https://jsonplaceholder.typicode.com/todos/1",
    "https://www.python.org",
    "https://invalid-url.abc",  # заведомо невалидный адрес для проверки
]

sem = asyncio.Semaphore(3) # ограничиваем параллельность

async def fetch(session, url, queue):
    async with sem:
        try:
            async with session.get(url) as resp:
                text = await resp.text()
                await queue.put((url, resp.status, text[:100]))
        except Exception as e:
            await queue.put((url, "ERROR", str(e)))

async def consumer(queue, results):
    while True:
        item = await queue.get()
        if item is None:
            break
        results.append(item)


async def main():
    queue = asyncio.Queue()
    results = []

    async with aiohttp.ClientSession() as session:
        producers = [fetch(session, url, queue) for url in URLS]
        consumer_task = asyncio.create_task(consumer(queue, results))

        await asyncio.gather(*producers)  # ждём все запросы
        await queue.put(None)  # сигнал для consumer
        await consumer_task  # ждём consumer

    for url, status, snippet in results:
        print(f"[{status}] {url}\n{snippet}\n{'-'*40}")

asyncio.run(main())

