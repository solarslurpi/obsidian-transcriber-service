import asyncio

async def my_task():
    try:
        print("Task started")
        await asyncio.sleep(5)  # Simulate work
        print("Task finished")
    except asyncio.CancelledError:
        print("Task was cancelled")

async def main():
    task = asyncio.create_task(my_task())
    await asyncio.sleep(2)  # Wait for a bit
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        print("Task cancellation confirmed")

asyncio.run(main())