__all__ = ['Uuid']


class Uuid:
    @classmethod
    def v4(cls):
        """Generates a random UUID v4"""
        from uuid import uuid4

        def generator():
            return uuid4()
        return generator

    @classmethod
    def v7(cls):
        """Generates a random UUID v7"""
        try:
            from uuid_utils import uuid7
        except ImportError:
            raise ImportError('Dependency "uuid_utils" must be installed to use UUID v7 generation.')

        def generator():
            return uuid7()

        return generator
