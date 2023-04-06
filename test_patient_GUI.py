import pytest
from testfixtures import LogCapture


@pytest.mark.parametrize("mrn, room_number, msg, met",
                         [("", "1", "Missing Patient Medical Record Number",
                           False),
                          ("1", "", "Missing Room Number", False),
                          ("1", "1", "Information Uploaded", True)
                          ])
def test_requirements_met(mrn, room_number, msg, met):
    from patient_GUI import requirements_met
    answer0, answer1 = requirements_met(mrn, room_number)
    assert answer0 == msg
    assert answer1 == met


@pytest.mark.parametrize("pressure, msg, met",
                         [("", "Information Uploaded", True),
                          ("A", "CPAP pressure is not an integer", False),
                          ("A1", "CPAP pressure is not an integer", False),
                          ("@1", "CPAP pressure is not an integer", False),
                          ("0", "CPAP Pressure is not between 4 and 25",
                           False),
                          ("-1", "CPAP Pressure is not between 4 and 25",
                           False),
                          ("3", "CPAP Pressure is not between 4 and 25",
                           False),
                          ("26", "CPAP Pressure is not between 4 and 25",
                           False),
                          ("99999", "CPAP Pressure is not between 4 and 25",
                           False),
                          ("4", "Information Uploaded", True),
                          ("25", "Information Uploaded", True)
                          ])
def test_validate_pressure(pressure, msg, met):
    from patient_GUI import validate_pressure
    answer0, answer1 = validate_pressure(pressure)
    assert answer0 == msg
    assert answer1 == met
