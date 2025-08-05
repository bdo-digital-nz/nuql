from nuql import Nuql


def test_client_init():
    n = Nuql()
    assert n.fields
