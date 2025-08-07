__all__ = ["Datetime"]

from datetime import datetime, timedelta, UTC


class Datetime:
    @classmethod
    def now(cls):
        """Generates current UTC time"""
        def generator():
            return datetime.now(UTC)
        return generator

    @classmethod
    def relative(
            cls,
            days: float = 0,
            seconds: float = 0,
            microseconds: float = 0,
            milliseconds: float = 0,
            minutes: float = 0,
            hours: float = 0,
            weeks: float = 0
    ):
        """Generates a UTC datetime relative to now."""
        def generator():
            return datetime.now(UTC) + timedelta(
                days=days,
                seconds=seconds,
                microseconds=microseconds,
                milliseconds=milliseconds,
                minutes=minutes,
                hours=hours,
                weeks=weeks
            )

        return generator
