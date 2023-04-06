import pytest


@pytest.mark.parametrize("data, expected",
                         [(["TURKEY", "END", "CHEESE", "END", "HAM", "END"],
                           [1, 3, 5]),
                          (["FUN", "END", "SMILE", "HAPPY", "END", "PEACE",
                            "LOVE", "END"], [1, 4, 7])])
def test_github_check(data, expected):
    from github_check import sample_function
    answer = sample_function(data, "END")
    assert answer == expected