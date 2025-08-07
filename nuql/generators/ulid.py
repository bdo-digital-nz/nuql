from ulid import ULID


class Ulid:
    @classmethod
    def now(cls):
        """Generates current ULID"""
        def generator():
            return ULID()
        return generator
