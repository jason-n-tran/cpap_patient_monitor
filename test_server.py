import pytest
from PatientModel import Patient, Session, Base, engine
from datetime import datetime


# Clean up database for tests
Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)


@pytest.mark.parametrize("in_data, expected_keys, expected_types, Error",
                         [({"patient_mrn": "123",
                            "patient_name": "Jason",
                            "pressure": "55"},
                           ["patient_mrn", "patient_name", "pressure"],
                           [int, str, int],
                           True),
                          ({"patient_mrn": 123,
                            "patient_name": "Jason",
                            "pressure": 55},
                           ["patient_mrn", "patient_name", "pressure"],
                           [int, str, int],
                           True),
                          ({"patient_mrn": "a123",
                            "patient_name": "Jason",
                            "pressure": "55"},
                           ["patient_mrn", "patient_name", "pressure"],
                           [int, str, int],
                           "Key patient_mrn is not an int or numeric string"),
                          ({"patient_mrn": "123",
                            "patient_name": "Jason",
                            "pressure": "a55"},
                           ["patient_mrn", "patient_name", "pressure"],
                           [int, str, int],
                           "Key pressure is not an int or numeric string"),
                          (["patient_mrn", "a123",
                            "patient_name", "Jason",
                            "pressure", "55"],
                           ["patient_mrn", "patient_name", "pressure"],
                           [int, str, int],
                           "Input is not a dictionary"),
                          ({"patient_mrn": "123",
                            "pressure": "55"},
                           ["patient_mrn", "patient_name", "pressure"],
                           [int, str, int],
                           "Key patient_name is missing from input"),
                          ({"patient_mrn": "123",
                            "patient_name": 3,
                            "pressure": "55"},
                           ["patient_mrn", "patient_name", "pressure"],
                           [int, str, int],
                           "Key patient_name has the incorrect value type")
                          ])
def test_validate_input_data_generic(in_data, expected_keys,
                                     expected_types, Error):
    from server import validate_input_data_generic
    answer = validate_input_data_generic(in_data, expected_keys,
                                         expected_types)
    assert answer == Error


def test_current_time():
    from server import current_time
    answer = current_time()
    assert answer == datetime.strftime(datetime.now(),
                                       "%Y-%m-%d %H:%M:%S")


@pytest.mark.parametrize("in_data, date",
                         [({"patient_name": "Jason",
                            "patient_mrn": 100,
                            "room_number": 100,
                            "CPAP_pressure": 10,
                            "breath_rate": 10.0,
                            "apnea_count": 10,
                            "flow_image": ""}, "2023-04-26 00:00:00"),
                          ({"patient_name": "",
                            "patient_mrn": 101,
                            "room_number": 101,
                            "CPAP_pressure": "",
                            "breath_rate": "",
                            "apnea_count": "",
                            "flow_image": ""}, "2023-04-26 00:00:00"),
                          ({"patient_name": "Jason",
                            "patient_mrn": 102,
                            "room_number": 102,
                            "CPAP_pressure": "",
                            "breath_rate": "",
                            "apnea_count": "",
                            "flow_image": ""}, "2023-04-26 00:00:00"),
                          ({"patient_name": "",
                            "patient_mrn": 103,
                            "room_number": 103,
                            "CPAP_pressure": 10,
                            "breath_rate": 10.0,
                            "apnea_count": 10,
                            "flow_image": ""}, "2023-04-26 00:00:00"),
                          ])
def test_add_patient_to_db(in_data, date):
    from server import new_patient_to_db
    answer0 = new_patient_to_db(in_data, date)
    session = Session()
    try:
        answer1 = session.query(Patient).filter_by(
            room_number=in_data["room_number"]
        ).first()
        assert answer1 is not None
        assert int(in_data["patient_mrn"]) == answer1.patient_mrn
        assert int(in_data["room_number"]) == answer1.room_number
    finally:
        session.close()


@pytest.mark.parametrize("patient_id, expected",
                         [(100, True),
                          (101, True),
                          (102, True),
                          (103, True),
                          (234, False)
                          ])
def test_does_patient_exist_in_db(patient_id, expected):
    from server import does_patient_exist_in_db
    answer = does_patient_exist_in_db(patient_id)
    assert answer == expected


@pytest.mark.parametrize("mrn, in_data, date",
                         [(100,
                           {"patient_name": "Tran",
                            "patient_mrn": 100,
                            "room_number": 100,
                            "CPAP_pressure": 11,
                            "breath_rate": 10.1,
                            "apnea_count": 11,
                            "flow_image": ""}, "2023-04-26 00:00:01"),
                          (101,
                           {"patient_name": "Tran",
                            "patient_mrn": 101,
                            "room_number": 101,
                            "CPAP_pressure": 11,
                            "breath_rate": 10.1,
                            "apnea_count": 11,
                            "flow_image": ""}, "2023-04-26 00:00:01"),
                          (102,
                           {"patient_name": "",
                            "patient_mrn": 102,
                            "room_number": 102,
                            "CPAP_pressure": 11,
                            "breath_rate": 10.1,
                            "apnea_count": 11,
                            "flow_image": ""}, "2023-04-26 00:00:01"),
                          (103,
                           {"patient_name": "Tran",
                            "patient_mrn": 301,
                            "room_number": 103,
                            "CPAP_pressure": "",
                            "breath_rate": "",
                            "apnea_count": "",
                            "flow_image": ""}, "2023-04-26 00:00:01")])
def test_update_patient(mrn, in_data, date):
    from server import update_patient
    answer0 = update_patient(mrn, in_data, date)
    session = Session()
    try:
        answer1 = session.query(Patient).filter_by(
            room_number=in_data["room_number"]
        ).first()
        assert answer1 is not None
        assert int(in_data["patient_mrn"]) == answer1.patient_mrn
        session.delete(answer1)
        session.commit()
    finally:
        session.close()


@pytest.mark.parametrize("in_data, msg, status",
                         [({"patient_name": "Jason",
                            "patient_mrn": 123,
                            "room_number": 123,
                            "CPAP_pressure": 10,
                            "breath_rate": 10.0,
                            "apnea_count": 10,
                            "flow_image": ""},
                           "New patient created", 200),
                          ({"patient_name": "Jason",
                            "patient_mrn": 123,
                            "room_number": 123,
                            "CPAP_pressure": 10,
                            "breath_rate": 10.0,
                            "apnea_count": 10,
                            "flow_image": ""},
                           "Patient successfully updated", 200),
                          ({"patient_name": "Jason",
                            "patient_mrn": "a123",
                            "room_number": 123,
                            "CPAP_pressure": 10,
                            "breath_rate": 10.0,
                            "apnea_count": 10,
                            "flow_image": ""},
                           "Key patient_mrn is not an int or numeric string",
                           400),
                          ({"patient_name": "Jason",
                            "patient_mrn": 123,
                            "room_number": 123,
                            "CPAP_pressure": 10,
                            "breath_rate": 10.0,
                            "apnea_count": "a10",
                            "flow_image": ""},
                           "Key apnea_count is not an int or numeric string",
                           400),
                          (["patient_name", "Jason",
                            "patient_mrn", 123,
                            "room_number", 123,
                            "CPAP_pressure", 10,
                            "breath_rate", 10.0,
                            "apnea_count", 10,
                            "flow_image", ""],
                           "Input is not a dictionary",
                           400),
                          ({"patient_mrn": 123,
                            "room_number": 123,
                            "CPAP_pressure": 10,
                            "breath_rate": 10.0,
                            "apnea_count": 10,
                            "flow_image": ""},
                           "Key patient_name is missing from input",
                           400),
                          ({"patient_name": 123,
                            "patient_mrn": 123,
                            "room_number": 123,
                            "CPAP_pressure": 10,
                            "breath_rate": 10.0,
                            "apnea_count": 10,
                            "flow_image": ""},
                           "Key patient_name has the incorrect value type",
                           400)
                          ])
def test_add_patient_driver(in_data, msg, status):
    from server import add_patient_driver
    answer0, answer1 = add_patient_driver(in_data)
    assert answer0 == msg
    assert answer1 == status


@pytest.mark.parametrize("room, cpap, result, code",
                         [(123, 10, 10, 200),
                          (234, 10, "Patient not in database", 400)
                          ])
def test_get_pressure_driver(room, cpap, result, code):
    from server import get_pressure_driver, post_new_cpap_pressure
    from server import cpap_pressure_updates
    cpap_pressure_updates.clear()
    post_new_cpap_pressure(room, cpap)
    answer0, answer1 = get_pressure_driver(room)
    assert answer0 == result
    assert answer1 == code


@pytest.mark.parametrize("room, cpap, pressure",
                         [(123, 10, 10)
                          ])
def test_get_pressure(room, cpap, pressure):
    from server import get_pressure, post_new_cpap_pressure
    from server import cpap_pressure_updates
    cpap_pressure_updates.clear()
    post_new_cpap_pressure(room, cpap)
    answer = get_pressure(room)
    session = Session()
    try:
        patient = session.query(Patient).filter_by(room_number=room).first()
        if patient is not None:
            session.delete(patient)
            session.commit()
    finally:
        session.close()
    assert answer == pressure
