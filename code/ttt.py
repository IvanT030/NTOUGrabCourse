import logging
import queue
import threading
import time
import random
import asyncio

items_queue = asyncio.Queue()
running = False

async def process_item():
    await items_queue.get()
    print('get!!')
    await asyncio.sleep(3)
    items_queue.task_done()

async def main():
    await items_queue.put('1')
    thread = threading.Thread(target=process_item)
    thread.start()
    await items_queue.join()
    thread.join()
    print('end')

asyncio.run(main())