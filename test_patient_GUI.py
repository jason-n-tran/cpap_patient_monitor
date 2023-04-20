import pytest
from testfixtures import LogCapture
import io
import base64
from matplotlib import pyplot as plt
from matplotlib.figure import Figure


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


def test_plot_to_b64():
    from patient_GUI import plot_to_b64
    fig = Figure(figsize=(14, 6))
    my_stringIObytes = io.BytesIO()
    fig.savefig(my_stringIObytes, format='jpg')
    my_stringIObytes.seek(0)
    my_base64_jpgData = base64.b64encode(my_stringIObytes.read())
    b64_string = str(my_base64_jpgData, encoding='utf-8')
    answer = plot_to_b64(fig)
    assert answer == b64_string


@pytest.mark.parametrize("mrn, room, name, pressure, rate, apnea, image, json",
                         [("", "", "", "", "", "", "",
                           {"patient_name": "",
                            "patient_mrn": "",
                            "room_number": "",
                            "CPAP_pressure": "",
                            "breath_rate": "",
                            "apnea_count": "",
                            "flow_image": ""}),
                          (1, 1, "", "", "", "", "",
                           {"patient_name": "",
                            "patient_mrn": 1,
                            "room_number": 1,
                            "CPAP_pressure": "",
                            "breath_rate": "",
                            "apnea_count": "",
                            "flow_image": ""}),
                          (1, 1, "Jason", "", "", "", "",
                           {"patient_name": "Jason",
                            "patient_mrn": 1,
                            "room_number": 1,
                            "CPAP_pressure": "",
                            "breath_rate": "",
                            "apnea_count": "",
                            "flow_image": ""}),
                          (1, 1, "Jason", 5, 3.3, 0, "",
                           {"patient_name": "Jason",
                            "patient_mrn": 1,
                            "room_number": 1,
                            "CPAP_pressure": 5,
                            "breath_rate": 3.3,
                            "apnea_count": 0,
                            "flow_image": ""})
                          ])
def test_create_json(mrn, room, name, pressure, rate, apnea, image, json):
    from patient_GUI import create_json
    answer = create_json(mrn, room, name, pressure, rate, apnea, image)
    assert answer == json


'''
@pytest.mark.parametrize("patient, status, text",
                         [({"patient_name": "",
                            "patient_mrn": "",
                            "room_number": "",
                            "CPAP_pressure": "",
                            "breath_rate": "",
                            "apnea_count": "",
                            "flow_image": ""}, 200, ""),
                          ({"patient_name": "",
                            "patient_mrn": 1,
                            "room_number": 1,
                            "CPAP_pressure": "",
                            "breath_rate": "",
                            "apnea_count": "",
                            "flow_image": ""}, 200, ""),
                          ({"patient_name": "Jason",
                            "patient_mrn": 1,
                            "room_number": 1,
                            "CPAP_pressure": "",
                            "breath_rate": "",
                            "apnea_count": "",
                            "flow_image": ""}, 200, ""),
                          ({"patient_name": "Jason",
                            "patient_mrn": 1,
                            "room_number": 1,
                            "CPAP_pressure": 5,
                            "breath_rate": 3.3,
                            "apnea_count": 0,
                            "flow_image": ""}, 200, "")
                          ])
def test_upload(patient, status, text):
    from server import app
    app.run()
    from patient_GUI import upload
    answer0, answer1 = upload(patient)
    assert answer0 == status
    assert answer1 == text
'''
