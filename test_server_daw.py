import pytest


@pytest.mark.parametrize("room_number, new_value, expected", [
    ("12", "14", True),
    ("1.2", "14", False),
    ("12", "1.4", False),
    ("Hello", "14", False),
    ("12", "Hello", False),
])
def test_validate_new_cpap_pressure_inputs(room_number, new_value, expected):
    from server import validate_new_cpap_pressure_inputs
    answer = validate_new_cpap_pressure_inputs(room_number, new_value)
    assert answer == expected


def test_post_new_cpap_pressure():
    from server import post_new_cpap_pressure
    from server import cpap_pressure_updates
    cpap_pressure_updates.clear()
    room_number = "12"
    new_value = "14"
    answer = post_new_cpap_pressure(room_number, new_value)
    answer_cpap_pressure_update = cpap_pressure_updates[12]
    cpap_pressure_updates.clear()
    assert answer_cpap_pressure_update == 14
    assert answer[0] == "Room number 12 CPAP pressure updated to 14"
    assert answer[1] == 200


def test_post_new_cpap_pressure_error():
    from server import post_new_cpap_pressure
    room_number = "1.2"
    new_value = "1.4"
    answer = post_new_cpap_pressure(room_number, new_value)
    assert answer[0] == "Bad value for room number or new value"
    assert answer[1] == 400
