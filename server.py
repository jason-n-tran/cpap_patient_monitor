from flask import Flask, request, jsonify
import ssl
from pymodm import connect
from PatientModel import Patient
from pymodm import errors as pymodm_errors
from secret import mongodb_acct, mongodb_pswd
import requests
import logging
from datetime import datetime


# Create an instance of the Flask server
app = Flask(__name__)


def init_server():
    """ Performs set-up functions before starting server
    This functions performs any needed set-up steps required for server
    operation.  The logging system is configured.  A connection is created
    to the MongoDB database.
    """
    logging.basicConfig(filename="log_file.log", filemode='w',
                        level=logging.INFO)
    connect("mongodb+srv://{}:{}@cluster0.ja8jerw.mongodb.net/final"
            "?retryWrites=true&w=majority"
            .format(mongodb_acct, mongodb_pswd), ssl_cert_reqs=ssl.CERT_NONE)


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
    does_id_exist = does_patient_exist_in_db(int(in_data["patient_mrn"]))
    date = current_time()
    if does_id_exist is False:
        # Do the work
        new_patient_to_db(in_data, date)
        # Return an answer
        return "New patient created", 200
    else:
        # Do the work
        update_patient(int(in_data["patient_mrn"]), in_data, date)
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


def does_patient_exist_in_db(mrn):
    """Determines whether a patient exists in the database based on a given id
    number
    This function accepts a patient id (medical record number) as an input
    parameter.  It then queries the MongoDB database, using the patient id
    as the primary key search parameter.  If the record does not exist, an
    exception will be thrown which is captured in a try/except block, allowing
    the function to return False, indicating that the record does not exist
    in the database.  If the record does exist, the function will return True.
    Parameters
    ----------
    mrn : int
        patient medical record number to search for in the database
    Returns
    ----------
    bool :
        True if patient exists in database, False otherwise
    """
    try:
        db_item = Patient.objects.raw({"_id": mrn}).first()
    except pymodm_errors.DoesNotExist:
        return False
    return True


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
    database under the key of the patient's MRN while converting the MRN
    and age entries to integers. The information sent to the database depends
    on whether a patient name was entered or if CPAP calculated data was
    entered or if both were entered. The database is hosted by mongoDB.
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
        None
    """
    if (in_data["patient_name"] != ""):
        if (in_data["CPAP_pressure"] != "" and in_data["breath_rate"] != ""):
            new_patient = Patient(patient_mrn=in_data["patient_mrn"],
                                  room_number=in_data["room_number"],
                                  patient_name=in_data["patient_name"],
                                  CPAP_pressure=[int(in_data["CPAP_pressure"]
                                                     )],
                                  breath_rate=[float(in_data["breath_rate"])],
                                  apnea_count=[int(in_data["apnea_count"])],
                                  flow_image=[str(in_data["flow_image"])],
                                  timestamp=[date])
        else:
            new_patient = Patient(patient_mrn=in_data["patient_mrn"],
                                  room_number=in_data["room_number"],
                                  patient_name=in_data["patient_name"])
    else:
        if (in_data["CPAP_pressure"] != "" and in_data["breath_rate"] != ""):
            new_patient = Patient(patient_mrn=in_data["patient_mrn"],
                                  room_number=in_data["room_number"],
                                  CPAP_pressure=[int(in_data["CPAP_pressure"]
                                                     )],
                                  breath_rate=[float(in_data["breath_rate"])],
                                  apnea_count=[int(in_data["apnea_count"])],
                                  flow_image=[str(in_data["flow_image"])],
                                  timestamp=[date])
        else:
            new_patient = Patient(patient_mrn=in_data["patient_mrn"],
                                  room_number=in_data["room_number"])
    saved_patient = new_patient.save()
    return saved_patient


def update_patient(mrn, in_data, date):
    """
    Updates existing patient information in database
    This function receives a patient dictionary then finds the corresponding
    patient entry in the database from the medical record number. It then
    updates the information stored based on whether a patient name was entered
    or if CPAP calculated data was entered or if both were entered. The
    database is hosted by mongoDB.
    Parameters
    ----------
    mrn : integer
        patient's medical record number
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
        None
    """
    x = Patient.objects.raw({"_id": mrn}).first()
    if (in_data["patient_name"] != ""):
        if (in_data["CPAP_pressure"] != "" and in_data["breath_rate"] != ""):
            x.patient_name = in_data["patient_name"]
            x.CPAP_pressure.append(int(in_data["CPAP_pressure"]))
            x.breath_rate.append(float(in_data["breath_rate"]))
            x.apnea_count.append(int(in_data["apnea_count"]))
            x.flow_image.append(str(in_data["flow_image"]))
            x.timestamp.append(date)
        else:
            x.patient_name = in_data["patient_name"]
    else:
        if (in_data["CPAP_pressure"] != "" and in_data["breath_rate"] != ""):
            x.CPAP_pressure.append(int(in_data["CPAP_pressure"]))
            x.breath_rate.append(float(in_data["breath_rate"]))
            x.apnea_count.append(int(in_data["apnea_count"]))
            x.flow_image.append(str(in_data["flow_image"]))
            x.timestamp.append(date)
    saved_patient = x.save()
    return saved_patient


@app.route("/CPAP_query/<mrn>", methods=["GET"])
def get_pressure_handler(mrn):
    """
    GET route to obtain CPAP pressure.
    This function implements a variable URL in which the server returns
    a patient's latest CPAP pressure. The variable URL will contain the MRN of
    the patient of interest. This MRN is passed to a driver function that will
    retrieve the data for this function to return.
    Parameters
    ----------
    mrn : integer or string
        patient's medical record number
    Returns
    -------
    answer : string
        Response message indicating type of error
    status_code : integer
        200 if successful and 400 if failed
    """
    answer, status = get_pressure_driver(mrn)
    return jsonify(answer), status


def get_pressure_driver(mrn):
    """
    Implements the '/CPAP_query/<mrn>' route
    This function performs the data validation and implementation for the
    `/CPAP_query/<mrn>` route which retrieves a patient's CPAP pressure
    data. It first validates that the patient MRN exists in the
    database. It then calls another function to retrieve the patient's
    information and returns the retrieved integer with status code 200
    Parameters
    ----------
    mrn : integer
        patient medical record number
    Returns
    -------
    string
        Response message indicating type of error or patient info if no error
    integer
        200 if successful and 400 if failed
    """
    # Validate input
    mrn_validation = does_patient_exist_in_db(int(mrn))
    if mrn_validation is not True:
        return "Patient not in database", 400
    # Do the work
    pressure = get_pressure(int(mrn))
    # Return an answer
    return pressure, 200


def get_pressure(mrn):
    """
    Obtains pressure data for specified patient.
    Takes a given patient's medical record number and obtains that patient's
    latest CPAP pressure value from the array in the database.
    Parameters
    ----------
    mrn : integer
        patient medical record number
    Returns
    -------
    integer
        latest CPAP pressure
    """
    x = Patient.objects.raw({"_id": mrn}).first()
    return x.CPAP_pressure[-1]


if __name__ == "__main__":
    init_server()
    app.run()
