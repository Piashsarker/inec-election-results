"""Agent pool for parallel processing of polling units.

This module provides the agent pool that manages concurrent processing
of multiple polling units using semaphore-based concurrency control.

Requirements: 6.5
"""
from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Generic, TypeVar

logger = logging.getLogger("inec_agent.agents.pool")

T = TypeVar("T")
R = TypeVar("R")


class TaskStatus(StrEnum):
    """Status of a task in the pool."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class PoolTask(Generic[T, R]):
    """A task to be processed by the agent pool.

    Attributes:
        id: Unique task identifier
        data: Task data to process
        status: Current task status
        result: Task result (if completed)
        error: Error message (if failed)
        attempts: Number of processing attempts
    """

    id: str
    data: T
    status: TaskStatus = TaskStatus.PENDING
    result: R | None = None
    error: str | None = None
    attempts: int = 0


@dataclass
class PoolStats:
    """Statistics for the agent pool.

    Attributes:
        total_tasks: Total number of tasks submitted
        pending_tasks: Number of pending tasks
        running_tasks: Number of currently running tasks
        completed_tasks: Number of completed tasks
        failed_tasks: Number of failed tasks
        cancelled_tasks: Number of cancelled tasks
    """

    total_tasks: int = 0
    pending_tasks: int = 0
    running_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    cancelled_tasks: int = 0

    def to_dict(self) -> dict[str, int]:
        """Convert stats to dictionary."""
        return {
            "total_tasks": self.total_tasks,
            "pending_tasks": self.pending_tasks,
            "running_tasks": self.running_tasks,
            "completed_tasks": self.completed_tasks,
            "failed_tasks": self.failed_tasks,
            "cancelled_tasks": self.cancelled_tasks,
        }


class AgentPool(Generic[T, R]):
    """Pool for parallel processing of tasks with concurrency control.

    This class manages a pool of concurrent tasks with:
    - Semaphore-based concurrency limiting
    - Task queue management
    - Progress tracking
    - Error handling and retry support

    Requirements: 6.5
    """

    def __init__(
        self,
        pool_size: int = 5,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ):
        """Initialize the agent pool.

        Args:
            pool_size: Maximum number of concurrent tasks
            max_retries: Maximum retry attempts for failed tasks
            retry_delay: Delay between retries in seconds
        """
        self.pool_size = pool_size
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        # Concurrency control
        self._semaphore = asyncio.Semaphore(pool_size)

        # Task management
        self._tasks: dict[str, PoolTask[T, R]] = {}
        self._task_queue: asyncio.Queue[str] = asyncio.Queue()
        self._running_tasks: dict[str, asyncio.Task] = {}

        # Control flags
        self._shutdown = False
        self._paused = False
        self._pause_event = asyncio.Event()
        self._pause_event.set()  # Not paused initially

        # Statistics
        self._stats = PoolStats()

        logger.info(f"AgentPool initialized with pool_size={pool_size}")

    async def submit(
        self,
        task_id: str,
        data: T,
    ) -> None:
        """Submit a task to the pool.

        Args:
            task_id: Unique task identifier
            data: Task data to process
        """
        if self._shutdown:
            raise RuntimeError("Pool is shut down")

        task = PoolTask[T, R](id=task_id, data=data)
        self._tasks[task_id] = task
        await self._task_queue.put(task_id)

        self._stats.total_tasks += 1
        self._stats.pending_tasks += 1

        logger.debug(f"Task {task_id} submitted to pool")

    async def submit_batch(
        self,
        tasks: list[tuple[str, T]],
    ) -> None:
        """Submit multiple tasks to the pool.

        Args:
            tasks: List of (task_id, data) tuples
        """
        for task_id, data in tasks:
            await self.submit(task_id, data)

    async def process_all(
        self,
        process_func: Callable[[T], Coroutine[Any, Any, R]],
        on_complete: Callable[[str, R], None] | None = None,
        on_error: Callable[[str, Exception], None] | None = None,
    ) -> dict[str, R]:
        """Process all submitted tasks.

        Args:
            process_func: Async function to process each task
            on_complete: Optional callback for completed tasks
            on_error: Optional callback for failed tasks

        Returns:
            Dictionary mapping task IDs to results
        """
        logger.info(f"Processing {self._stats.pending_tasks} tasks")

        results: dict[str, R] = {}

        async def process_task(task_id: str) -> None:
            """Process a single task with semaphore control."""
            # Wait if paused
            await self._pause_event.wait()

            # Check for shutdown
            if self._shutdown:
                return

            task = self._tasks.get(task_id)
            if not task:
                return

            async with self._semaphore:
                # Update stats
                self._stats.pending_tasks -= 1
                self._stats.running_tasks += 1
                task.status = TaskStatus.RUNNING

                try:
                    task.attempts += 1
                    result = await process_func(task.data)

                    task.result = result
                    task.status = TaskStatus.COMPLETED
                    results[task_id] = result

                    self._stats.completed_tasks += 1

                    if on_complete:
                        on_complete(task_id, result)

                    logger.debug(f"Task {task_id} completed successfully")

                except Exception as e:
                    logger.error(f"Task {task_id} failed: {e}")

                    # Retry if attempts remaining
                    if task.attempts < self.max_retries:
                        logger.info(f"Retrying task {task_id} (attempt {task.attempts + 1})")
                        await asyncio.sleep(self.retry_delay * task.attempts)
                        await self._task_queue.put(task_id)
                        self._stats.pending_tasks += 1
                        task.status = TaskStatus.PENDING
                    else:
                        task.error = str(e)
                        task.status = TaskStatus.FAILED
                        self._stats.failed_tasks += 1

                        if on_error:
                            on_error(task_id, e)

                finally:
                    self._stats.running_tasks -= 1

        # Create tasks for all queued items
        processing_tasks = []
        while not self._task_queue.empty():
            task_id = await self._task_queue.get()
            processing_tasks.append(asyncio.create_task(process_task(task_id)))
            self._running_tasks[task_id] = processing_tasks[-1]

        # Wait for all tasks to complete
        if processing_tasks:
            await asyncio.gather(*processing_tasks, return_exceptions=True)

        logger.info(
            f"Processing complete: {self._stats.completed_tasks} completed, "
            f"{self._stats.failed_tasks} failed"
        )

        return results

    async def process_batch(
        self,
        items: list[T],
        process_func: Callable[[T], Coroutine[Any, Any, R]],
        id_func: Callable[[T], str] | None = None,
    ) -> list[R]:
        """Process a batch of items in parallel.

        This is a convenience method that submits all items and processes them.

        Args:
            items: List of items to process
            process_func: Async function to process each item
            id_func: Optional function to generate task IDs from items

        Returns:
            List of results in the same order as input items
        """
        # Generate task IDs
        if id_func:
            task_ids = [id_func(item) for item in items]
        else:
            task_ids = [str(i) for i in range(len(items))]

        # Submit all tasks
        for task_id, item in zip(task_ids, items):
            await self.submit(task_id, item)

        # Process all tasks
        results_dict = await self.process_all(process_func)

        # Return results in order
        return [results_dict.get(task_id) for task_id in task_ids]

    def pause(self) -> None:
        """Pause processing of new tasks."""
        logger.info("Pausing agent pool")
        self._paused = True
        self._pause_event.clear()

    def resume(self) -> None:
        """Resume processing of tasks."""
        logger.info("Resuming agent pool")
        self._paused = False
        self._pause_event.set()

    def is_paused(self) -> bool:
        """Check if the pool is paused.

        Returns:
            True if paused
        """
        return self._paused

    async def shutdown(self, wait: bool = True) -> None:
        """Shutdown the pool.

        Args:
            wait: Whether to wait for running tasks to complete
        """
        logger.info("Shutting down agent pool")
        self._shutdown = True

        # Resume if paused to allow tasks to check shutdown flag
        if self._paused:
            self.resume()

        if wait:
            # Wait for running tasks
            if self._running_tasks:
                await asyncio.gather(
                    *self._running_tasks.values(),
                    return_exceptions=True
                )
        else:
            # Cancel running tasks
            for task in self._running_tasks.values():
                if not task.done():
                    task.cancel()

    def get_task(self, task_id: str) -> PoolTask[T, R] | None:
        """Get a task by ID.

        Args:
            task_id: Task identifier

        Returns:
            PoolTask or None if not found
        """
        return self._tasks.get(task_id)

    def get_stats(self) -> PoolStats:
        """Get pool statistics.

        Returns:
            PoolStats object
        """
        return self._stats

    def get_failed_tasks(self) -> list[PoolTask[T, R]]:
        """Get all failed tasks.

        Returns:
            List of failed PoolTask objects
        """
        return [
            task for task in self._tasks.values()
            if task.status == TaskStatus.FAILED
        ]

    def get_completed_tasks(self) -> list[PoolTask[T, R]]:
        """Get all completed tasks.

        Returns:
            List of completed PoolTask objects
        """
        return [
            task for task in self._tasks.values()
            if task.status == TaskStatus.COMPLETED
        ]

    def reset(self) -> None:
        """Reset the pool state."""
        self._tasks.clear()
        self._task_queue = asyncio.Queue()
        self._running_tasks.clear()
        self._shutdown = False
        self._paused = False
        self._pause_event.set()
        self._stats = PoolStats()

        logger.info("Agent pool reset")


class PollingUnitPool(AgentPool[dict[str, Any], dict[str, Any]]):
    """Specialized agent pool for processing polling units.

    This pool is configured for processing election result data
    from polling units with appropriate defaults.
    """

    def __init__(
        self,
        pool_size: int = 5,
        max_retries: int = 3,
    ):
        """Initialize the polling unit pool.

        Args:
            pool_size: Maximum concurrent polling units to process
            max_retries: Maximum retry attempts for failed units
        """
        super().__init__(
            pool_size=pool_size,
            max_retries=max_retries,
            retry_delay=2.0,  # Longer delay for network operations
        )

    async def process_polling_units(
        self,
        polling_units: list[dict[str, Any]],
        process_func: Callable[[dict[str, Any]], Coroutine[Any, Any, dict[str, Any]]],
    ) -> dict[str, dict[str, Any]]:
        """Process a list of polling units.

        Args:
            polling_units: List of polling unit dictionaries
            process_func: Async function to process each polling unit

        Returns:
            Dictionary mapping polling unit IDs to results
        """
        # Submit all polling units
        for pu in polling_units:
            pu_id = pu.get("id") or pu.get("polling_unit", {}).get("id", "")
            if pu_id:
                await self.submit(pu_id, pu)

        # Process all
        return await self.process_all(process_func)
