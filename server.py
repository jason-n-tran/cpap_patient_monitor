from flask import Flask, request, jsonify
from PatientModel import Patient, Session
import requests
import logging
from datetime import datetime
import json


# Create an instance of the Flask server
app = Flask(__name__)
# Dictionary to hold requested updates from the monitoring side to CPAP
#   pressures.  Key will be a room number (integer).  Value will be an integer
#   containing the newly requested CPAP pressure.
cpap_pressure_updates = {}


def init_server():
    """ Performs set-up functions before starting server
    This functions performs any needed set-up steps required for server
    operation.  The logging system is configured.  The SQLite database
    is initialized through the PatientModel import.
    """
    logging.basicConfig(filename="log_file.log", filemode='w',
                        level=logging.INFO)


@app.route("/add_patient", methods=["POST"])
def add_patient_handler():
    """
    Flask Handler for /add_patient route
    POST route to receive information about a new patient and add the
    patient to the database. This "Flask handler" function receives a POST
    request to add a new patient to the database. The POST request should
    receive a dictionary encoded as a JSON string in the following format:
        {"patient_name": <patient_name>,
        "patient_mrn": <medical_record_number>,
        "room_number": <room_number>,
        "CPAP_pressure": <CPAP_pressure>,
        "breath_rate": <breath_rate>,
        "apnea_count": <apnea_count>,
        "flow_image": <flow_b64_string>}
    Receives the dictionary sent from POST request and calls on patient
    driver to validate dictionary and add to database. Returns a response
    message and corresponding status code.
    Returns
    -------
    answer : string
        Response message indicating type of error
    status_code : integer
        200 if successful and 400 if failed
    """
    # Receive data from POST request
    in_data = request.get_json()
    # Call other functions to do the work
    answer, status_code = add_patient_driver(in_data)
    # Return a response
    return jsonify(answer), status_code


def add_patient_driver(in_data):
    """
    Implements the 'add_patient' route
    This function performs the data validation and implementation for the
    `add_patient` route which adds a new patient to the database. It
    first calls a function that validates that the input data to the route is a
    dictionary that has the necessary keys and value data types.  If the
    necessary information does not exist, the function returns an error message
    and a status code of 400.  Otherwise, it checks whether the patient already
    exists in the database. If not, another function is called and sent
    the necessary information to add a new patient to the database. If the
    patient already exists, the information will be updated. A success
    message and a 200 status code is then returned.
    Parameters
    ----------
    in_data : dictionary
        Patient dictionary in the format:
        {"patient_name": <patient_name>,
        "patient_mrn": <medical_record_number>,
        "room_number": <room_number>,
        "CPAP_pressure": <CPAP_pressure>,
        "breath_rate": <breath_rate>,
        "apnea_count": <apnea_count>,
        "flow_image": <flow_b64_string>}
    Returns
    -------
    validation : string
        Response message indicating type of error or "Patient successfully
        updated" if no error
    : integer
        200 if successful and 400 if failed
    """
    # Validate input
    expected_keys = ["patient_mrn", "room_number", "patient_name",
                     "CPAP_pressure", "breath_rate", "apnea_count",
                     "flow_image"]
    expected_types = [int, int, str, int, float, int, str]
    validation = validate_input_data_generic(in_data, expected_keys,
                                             expected_types)
    if validation is not True:
        return validation, 400
    does_id_exist = does_patient_exist_in_db(int(in_data["room_number"]))
    date = current_time()
    if does_id_exist is False:
        # Do the work
        new_patient_to_db(in_data, date)
        # Return an answer
        return "New patient created", 200
    else:
        # Do the work
        update_patient(int(in_data["room_number"]), in_data, date)
        # Return an answer
        return "Patient successfully updated", 200


def validate_input_data_generic(in_data, expected_keys, expected_types):
    """
    Validates that input data is a dictionary with correct information
    This function receives the data that was sent with a POST request.  It
    also receives lists of the keys and value data types that are expected to
    be in this dictionary. The function first verifies that the data sent to
    the post request is a dictionary. Then, it verifies that the expected keys
    are found in the dictionary and that the corresponding value data types
    are of the correct type. In the case of integers, it also checks whether
    the value can be converted to a valid integer. An error message is returned
    if the data is not a dictionary, a key is missing or there is an invalid
    data type. If keys and data types are correct, a value of True is returned.
    It ignores empty strings and checks that floats could be numeric strings.
    Parameters
    ----------
    in_data : dict
        object received by the POST request
    expected_keys : list
        keys that should be found in the POST request dictionary
    expected_types : list
        the value data types that should be found in the POST request
        dictionary
    Returns
    -------
        str: error message if there is a problem with the input data, or
        bool: True if input data is valid.
    """
    if type(in_data) is not dict:
        return "Input is not a dictionary"
    for key, value_type in zip(expected_keys, expected_types):
        if key not in in_data:
            return "Key {} is missing from input".format(key)
        if in_data[key] == "":
            continue
        if type(in_data[key]) is not value_type:
            if value_type == float:
                try:
                    float(in_data[key])
                    continue
                except ValueError:
                    return "Key {} is not an int or numeric string".format(key)
            if value_type == int:
                if str(in_data[key]).isnumeric() is False:
                    return "Key {} is not an int or numeric string".format(key)
            else:
                return "Key {} has the incorrect value type".format(key)
    return True


def does_patient_exist_in_db(room_number):
    """Determines whether a patient exists in the database based on a given id
    number
    This function accepts a patient room number as an input
    parameter.  It then queries the SQLite database, using the room number
    as the primary key search parameter.  If the record does not exist,
    the function will return False, indicating that the record does not exist
    in the database.  If the record does exist, the function will return True.
    Parameters
    ----------
    room_number : int
        patient room number to search for in the database
    Returns
    ----------
    bool :
        True if patient exists in database, False otherwise
    """
    session = Session()
    try:
        patient = session.query(Patient).filter_by(
            room_number=room_number).first()
        return patient is not None
    finally:
        session.close()


def current_time():
    """
    Returns the current time formatted as "Year-month-day hour:minute:seconds"
    Parameters
    ----------
    None
    Returns
    -------
    string:
        current time formatted as "Year-month-day hour:minute:seconds"
    """
    return datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S")


def new_patient_to_db(in_data, date):
    """
    Adds a new patient dictionary to the database
    This function receives a patient dictionary then adds an entry to the
    database under the key of the patient's room number while converting
    the MRN
    and age entries to integers. The information sent to the database depends
    on whether a patient name was entered or if CPAP calculated data was
    entered or if both were entered. The database uses SQLite.
    Parameters
    ----------
    patient_dic : dictioanry
        Patient dictionary in the format:
        {"patient_name": <patient_name>,
        "patient_mrn": <medical_record_number>,
        "room_number": <room_number>,
        "CPAP_pressure": <CPAP_pressure>,
        "breath_rate": <breath_rate>,
        "apnea_count": <apnea_count>,
        "flow_image": <flow_b64_string>}
    date : string
        current time formatted as "Year-month-day hour:minute:seconds"
    Returns
    -------
        Patient object
    """
    session = Session()
    try:
        if (in_data["patient_name"] != ""):
            if (in_data["CPAP_pressure"] !=
                    "" and in_data["breath_rate"] != ""):
                new_patient = Patient(
                    patient_mrn=in_data["patient_mrn"],
                    room_number=in_data["room_number"],
                    patient_name=in_data["patient_name"],
                    CPAP_pressure=json.dumps([int(in_data["CPAP_pressure"])]),
                    breath_rate=json.dumps([float(in_data["breath_rate"])]),
                    apnea_count=json.dumps([int(in_data["apnea_count"])]),
                    flow_image=json.dumps([str(in_data["flow_image"])]),
                    timestamp=json.dumps([date])
                )
            else:
                new_patient = Patient(
                    patient_mrn=in_data["patient_mrn"],
                    room_number=in_data["room_number"],
                    patient_name=in_data["patient_name"]
                )
        else:
            if (in_data["CPAP_pressure"] !=
                    "" and in_data["breath_rate"] != ""):
                new_patient = Patient(
                    patient_mrn=in_data["patient_mrn"],
                    room_number=in_data["room_number"],
                    CPAP_pressure=json.dumps([int(in_data["CPAP_pressure"])]),
                    breath_rate=json.dumps([float(in_data["breath_rate"])]),
                    apnea_count=json.dumps([int(in_data["apnea_count"])]),
                    flow_image=json.dumps([str(in_data["flow_image"])]),
                    timestamp=json.dumps([date])
                )
            else:
                new_patient = Patient(
                    patient_mrn=in_data["patient_mrn"],
                    room_number=in_data["room_number"]
                )
        session.add(new_patient)
        session.commit()
        return new_patient
    finally:
        session.close()


def update_patient(room_number, in_data, date):
    """
    Updates existing patient information in database
    This function receives a patient dictionary then finds the corresponding
    patient entry in the database from the room number. It then
    updates the information stored based on whether a patient name was entered
    or if CPAP calculated data was entered or if both were entered. The
    database uses SQLite. If the patient medical record number is
    different from the one in the database for the specified room, the old
    patient information is deleted and a new patient is created for the most
    recent patient that is in that room.
    Parameters
    ----------
    room_number : integer
        patient's room number
    patient_dic : dictioanry
        Patient dictionary in the format:
        {"patient_name": <patient_name>,
        "patient_mrn": <medical_record_number>,
        "room_number": <room_number>,
        "CPAP_pressure": <CPAP_pressure>,
        "breath_rate": <breath_rate>,
        "apnea_count": <apnea_count>,
        "flow_image": <flow_b64_string>}
    date : string
        current time formatted as "Year-month-day hour:minute:seconds"
    Returns
    -------
        Patient object
    """
    session = Session()
    try:
        x = session.query(Patient).filter_by(room_number=room_number).first()
        if (x.patient_mrn != in_data["patient_mrn"]):
            session.delete(x)
            session.commit()
            patient = new_patient_to_db(in_data, date)
            return patient
        if (in_data["patient_name"] != ""):
            if (in_data["CPAP_pressure"] !=
                    "" and in_data["breath_rate"] != ""):
                x.patient_name = in_data["patient_name"]
                cpap_list = json.loads(
                    x.CPAP_pressure) if x.CPAP_pressure else []
                cpap_list.append(int(in_data["CPAP_pressure"]))
                x.CPAP_pressure = json.dumps(cpap_list)

                breath_list = json.loads(
                    x.breath_rate) if x.breath_rate else []
                breath_list.append(float(in_data["breath_rate"]))
                x.breath_rate = json.dumps(breath_list)

                apnea_list = json.loads(x.apnea_count) if x.apnea_count else []
                apnea_list.append(int(in_data["apnea_count"]))
                x.apnea_count = json.dumps(apnea_list)

                flow_list = json.loads(x.flow_image) if x.flow_image else []
                flow_list.append(str(in_data["flow_image"]))
                x.flow_image = json.dumps(flow_list)

                time_list = json.loads(x.timestamp) if x.timestamp else []
                time_list.append(date)
                x.timestamp = json.dumps(time_list)
            else:
                x.patient_name = in_data["patient_name"]
        else:
            if (in_data["CPAP_pressure"] !=
                    "" and in_data["breath_rate"] != ""):
                cpap_list = json.loads(
                    x.CPAP_pressure) if x.CPAP_pressure else []
                cpap_list.append(int(in_data["CPAP_pressure"]))
                x.CPAP_pressure = json.dumps(cpap_list)

                breath_list = json.loads(
                    x.breath_rate) if x.breath_rate else []
                breath_list.append(float(in_data["breath_rate"]))
                x.breath_rate = json.dumps(breath_list)

                apnea_list = json.loads(x.apnea_count) if x.apnea_count else []
                apnea_list.append(int(in_data["apnea_count"]))
                x.apnea_count = json.dumps(apnea_list)

                flow_list = json.loads(x.flow_image) if x.flow_image else []
                flow_list.append(str(in_data["flow_image"]))
                x.flow_image = json.dumps(flow_list)

                time_list = json.loads(x.timestamp) if x.timestamp else []
                time_list.append(date)
                x.timestamp = json.dumps(time_list)
        session.commit()
        return x
    finally:
        session.close()


@app.route("/CPAP_query/<room_number>", methods=["GET"])
def get_pressure_handler(room_number):
    """
    GET route to obtain CPAP pressure.
    This function implements a variable URL in which the server returns
    a patient's latest CPAP pressure. The variable URL will contain the MRN of
    the patient of interest. This MRN is passed to a driver function that will
    retrieve the data for this function to return.
    Parameters
    ----------
    room_number : integer or string
        patient's room number
    Returns
    -------
    answer : string
        Response message indicating type of error
    status_code : integer
        200 if successful and 400 if failed
    """
    answer, status = get_pressure_driver(room_number)
    return jsonify(answer), status


def get_pressure_driver(room_number):
    """
    Implements the '/CPAP_query/<room_number>' route
    This function performs the data validation and implementation for the
    `/CPAP_query/<room_number>` route which retrieves a patient's CPAP pressure
    data. It first validates that the room number exists in the
    database. It then calls another function to retrieve the patient's
    information and returns the retrieved integer with status code 200
    Parameters
    ----------
    room_number : integer
        patient room number
    Returns
    -------
    string
        Response message indicating type of error or patient info if no error
    integer
        200 if successful and 400 if failed
    """
    # Validate input
    mrn_validation = does_patient_exist_in_db(int(room_number))
    if mrn_validation is not True:
        return "Patient not in database", 400
    # Do the work
    pressure = get_pressure(int(room_number))
    # Return an answer
    return pressure, 200


def get_pressure(room_number):
    """
    Obtains pressure data for specified room_number.
    Takes a given patient's room number and obtains that patient's
    latest CPAP pressure value from the array in the database.
    Parameters
    ----------
    room_number : integer
        patient room number
    Returns
    -------
    integer
        latest CPAP pressure
    """
    return cpap_pressure_updates[room_number]


@app.route("/new_cpap_pressure/<room_number>/<new_value>", methods=["GET"])
def post_new_cpap_pressure(room_number, new_value):
    """Receives requests for updated CPAP pressures for a specific room

    The monitoring station should have the ability to request an updated
    CPAP pressure for a specific room.  This route receives this request.  It
    uses a variable URL to receive the room number and updated value for the
    CPAP pressure.  The room number and updated CPAP pressure will be received
    as strings from the variable URL and these strings should contain an
    integer value.  If the inputs do not pass validation, an error message is
    returned along with a 400 status code.  if the inputs do pass validation,
    the numeric strings are converted to integers and added to the
    "cpap_pressure_updates" dictionary using the room number as the key and
    the new value as the value.  The patient-side client can then call a route
    which will access this "cpap_pressure_updates" dictionary and see if a new
    value is available for a specific room number.

    Parameters
    ----------
    room_number : string
        A numeric string containing the room number as an integer that should
        receive an updated CPAP pressure
    new_value : string
        A numeric string containing an updated CPAP pressure as an integer

    Returns
    -------
    string, integer
        A message about the success or failure of the route and a status code

    """
    if validate_new_cpap_pressure_inputs(room_number, new_value) is False:
        return "Bad value for room number or new value", 400
    cpap_pressure_updates[int(room_number)] = int(new_value)
    print(cpap_pressure_updates)
    return "Room number {} CPAP pressure updated to {}"\
        .format(int(room_number), int(new_value)), 200


def validate_new_cpap_pressure_inputs(room_number, new_value):
    """Validates input to the "/new_cpap_pressure/<room_number>/<new_value>"
    route

    The "/new_cpap_pressure/<room_number>/<new_value>" route is a GET request
    with a variable URL.  The "room_number" and "new_value" should contain
    integers as a string from the variable URL.  This function attempts to
    convert these strings into integers.  If either string does not contain an
    integer, the ValueError exception will be raised and captured and a value
    of False will be returned.  If no exceptions are raised, the strings must
    contain the desired integers, and a value of True is returned.

    Parameters
    ----------
    room_number : string
        The portion of the variable URL for the room number for validation
    new_value : string
        The portion of the variable URL for the new CPAP pressure for
        validation

    Returns
    -------
    boolean
        True if validation is successful, False if not
    """
    try:
        room_no = int(room_number)
        new_value = int(new_value)
    except ValueError:
        return False
    return True


@app.route("/health", methods=["GET"])
def health_check():
    """
    Health check endpoint for Docker and monitoring
    Returns a simple JSON response indicating the service is running.

    Returns
    -------
    dict
        Health status message
    integer
        200 status code
    """
    return jsonify({"status": "healthy", "service": "sleep-lab-api"}), 200


@app.route("/get_all_patients", methods=["GET"])
def get_all_patients_handler():
    """
    Flask Handler for /get_all_patients route
    GET route to retrieve information about all patients in the database.
    This route queries the database for all patient records and returns them
    as a JSON array with all patient information including deserialized arrays.

    Returns
    -------
    answer : list
        List of patient dictionaries with all information
    status_code : integer
        200 if successful and 400 if failed
    """
    answer, status_code = get_all_patients_driver()
    return jsonify(answer), status_code


def get_all_patients_driver():
    """
    Implements the 'get_all_patients' route
    This function retrieves all patient records from the database and formats
    them into a list of dictionaries. Each dictionary contains all patient
    information with JSON arrays deserialized into Python lists.

    Returns
    -------
    list
        List of patient dictionaries, or error message string
    integer
        200 if successful and 400 if failed
    """
    session = Session()
    try:
        patients = session.query(Patient).all()
        patient_list = []
        for patient in patients:
            patient_dict = {
                "room_number": patient.room_number,
                "patient_mrn": patient.patient_mrn,
                "patient_name": (
                    patient.patient_name if patient.patient_name
                    else "Not provided"
                ),
                "CPAP_pressure": json.loads(
                    patient.CPAP_pressure) if patient.CPAP_pressure else [],
                "breath_rate": json.loads(
                    patient.breath_rate) if patient.breath_rate else [],
                "apnea_count": json.loads(
                    patient.apnea_count) if patient.apnea_count else [],
                "flow_image": json.loads(
                    patient.flow_image) if patient.flow_image else [],
                "timestamp": json.loads(
                        patient.timestamp) if patient.timestamp else []}
            patient_list.append(patient_dict)
        return patient_list, 200
    except Exception as e:
        return "Error retrieving patients: {}".format(str(e)), 400
    finally:
        session.close()


if __name__ == "__main__":
    init_server()
    app.run(host='0.0.0.0', port=5000, debug=False)
