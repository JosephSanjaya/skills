import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AsyncTaskGroup")


async def fetch_service_a() -> str:
    await asyncio.sleep(0.5)
    return "Service A Data"


async def fetch_service_b() -> str:
    await asyncio.sleep(0.1)
    raise ValueError("Service B encountered an error")


async def orchestrate_services() -> None:
    try:
        # TaskGroup cancels sibling tasks if any task raises an exception
        async with asyncio.TaskGroup() as tg:
            task_a = tg.create_task(fetch_service_a())
            task_b = tg.create_task(fetch_service_b())

        logger.info(f"Results: {task_a.result()}, {task_b.result()}")
    except* ValueError as eg:
        for error in eg.exceptions:
            logger.error(f"Captured ValueError: {error}")


if __name__ == "__main__":
    asyncio.run(orchestrate_services())
