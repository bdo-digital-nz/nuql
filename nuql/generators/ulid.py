from nuql import NuqlError


class Ulid:
    @classmethod
    def now(cls):
        """Generates current ULID"""
        try:
            import ulid
        except ImportError:
            raise NuqlError(
                code='DependencyError',
                message='The "python-ulid" package is required to use the ULID field.'
            )

        def generator():
            return ulid.ULID()

        return generator
