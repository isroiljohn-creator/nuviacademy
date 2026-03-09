"""Analytics middleware — auto-tracks user activity."""
from typing import Callable, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject


class AnalyticsMiddleware(BaseMiddleware):
    """Middleware to track user activity timestamps."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        # You can add activity tracking here (last_seen, etc.)
        return await handler(event, data)
