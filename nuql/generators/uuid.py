__all__ = ['Uuid']

from uuid_utils import uuid4, uuid7


class Uuid:
    @classmethod
    def v4(cls):
        """Generates a random UUID v4"""
        def generator():
            return uuid4()
        return generator

    @classmethod
    def v7(cls):
        """Generates a random UUID v7"""
        def generator():
            return uuid7()
        return generator
