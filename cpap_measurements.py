import logging
import json
import numpy as np
import matplotlib.pyplot as plt
from scipy import signal
from scipy import integrate


def error_check(line):
    """Logs errors if a line has missing or incorrect data points

    From each time point line, creates an array of seven entries by
    separating at each comma. Checks each of the seven entries to
    ensure that it is not missing a value, contains a non-numeric string,
    or is NaN in which case it would log an error with the message "Incorrect
    Data" and return False to signal to skip the line. Otherwise, returns
    True to indicate that all seven data points are valid.

    Parameters
    ----------
    line : string
        One line of the input file containing data for a single time point

    Returns
    -------
    valid : boolean
        True if all seven values on a line are numeric and usable
    """
    data = line.split(",")
    valid = True
    for x in data:
        if (x == ""):
            logging.error("Incorrect Data")
            valid = False
        elif (x == "NaN"):
            logging.error("Incorrect Data")
            valid = False
        else:
            try:
                val = float(x)
            except ValueError:
                logging.error("Incorrect Data")
                valid = False
    return valid


def ADC_to_Pressure(line):
    """Converts each ADC value to Pressure

    Given a time points data, ignores time value and converts the other six
    values from ADC integer units to float pressure values in Pascals

    Parameters
    ----------
    line : string
        One line of the input file containing data for a single time point

    Returns
    -------
    data : array of seven floats
        Index one is time, index two is patient p2, index 3 is patient
        p1ins, index 4 is patient p1exp, index 5 is CPAP p2, index 6 is
        CPAP p1ins, index 6 is CPAP p1exp
    """
    data = line.split(",")
    for i in range(7):
        if i == 0:
            data[i] = float(data[i])
        else:
            data[i] = 98.0665 * (25.4 / (14745 - 1638)) * (int(data[i]) - 1638)
    return data


def Pressure_to_Flow(data):
    """Converts each Pressure value to Volumetric Flow

    Given a time points data, compares inspiration pressure with expiration
    pressure to determine whether the flow is in or out and calculates the
    flow as a positive value for inspiration and a negative value for
    expiration using the formula for venturi tubes with upstream diameter
    of 15 mm, neck diameter of 12 mm, and moist air density of 1.199 kg/m^3.

    Parameters
    ----------
    data : array of seven floats
        Index one is time, index two is patient p2, index 3 is patient
        p1ins, index 4 is patient p1exp, index 5 is CPAP p2, index 6 is
        CPAP p1ins, index 6 is CPAP p1exp

    Returns
    -------
    data[0] : float
        Time point in seconds
    flow : float
        Calculated volumetric flow rate in m^3/second
    """
    p2 = data[1]
    p1_ins = data[2]
    p1_exp = data[3]
    A1 = np.pi * (0.0075)**2
    A2 = np.pi * (0.006)**2
    if (p1_ins >= p1_exp):
        flow = A1 * np.sqrt(2 * (p1_ins - p2) / (1.199 * (((A1 / A2)**2) - 1)))
    if (p1_ins < p1_exp):
        flow = -A1 * np.sqrt(2 * (p1_exp - p2) /
                             (1.199 * (((A1 / A2)**2) - 1)))
    return data[0], flow


def find_breaths(time, flow):
    """Finds the number of breaths and the time at which they occured

    Takes time vs. flow data and uses scipy find_peaks function to find
    peaks that satisfy parameters adjusted to identify respiration data.
    Compares each positive peak to see if there is a corresponding negative
    peak occuring after it before another positive peak. Stores the peak
    otherwise. If there is a consecutive inhalation and expiration, it will
    store the breath time of the peak with the highest flow and add one to
    the breath count.

    Parameters
    ----------
    time : array of float
        Time points in seconds
    flow : array of float
        Calculated volumetric flow rates in m^3/second

    Returns
    -------
    breaths : integer
        Number of breaths in data as defined
    breath_times : array of floats
        All the time points at which a positive peak of a breath was recorded
    """
#    plt.plot(time, flow)
    ins_peaks, ins_properties = signal.find_peaks(flow, .0001,
                                                  None, 80, None, 20)
    exp_peaks, exp_properties = signal.find_peaks(-flow, .00005,
                                                  None, 80, None, 20)
#    for x in ins_peaks:
#        plt.plot(time[x], flow[x], 'r.')
#    for y in exp_peaks:
#        plt.plot(time[y], flow[y], 'b.')
    breaths = 1
    breath_times = []
    pos_breaths = dict()
    for i in range(len(ins_peaks) - 1):
        for z in exp_peaks:
            if ((time[ins_peaks[i]] < time[z]) and
                    (time[z] < time[ins_peaks[i + 1]])):
                breaths += 1
                pos_breaths.update({flow[ins_peaks[i]]: i})
                actual_peak = max(pos_breaths.keys())
                breath_times.append(time[ins_peaks[pos_breaths[actual_peak]]])
                pos_breaths.clear()
                break
            else:
                pos_breaths.update({flow[ins_peaks[i]]: i})
    breath_times.append(time[ins_peaks[i + 1]])
#    for z in breath_times:
#        plt.axvline(z, color = "r")
#    plt.show(block=True)
    return breaths, breath_times


def calculate_duration(time):
    """Calculates duration of data in seconds

    Takes all time points collected and finds duration by subtracting
    first time point from last time point in seconds

    Parameters
    ----------
    time : array of float
        Time points in seconds

    Returns
    -------
    duration : float
        Time duration of data in seconds
    """
    duration = time[-1] - time[0]
    return duration


def calculate_breath_rate(duration, breaths):
    """Calculates breath rate of patient

    Converts duration of patient's time data from seconds to minutes then
    calculates breath rate as quotient of number of breaths taken divided
    by duration

    Parameters
    ----------
    duration : float
        Time duration of data in seconds
    breaths : integer
        Number of breaths in data as defined

    Returns
    -------
    breath_rate : float
        Average breathing rate from data in breaths per minute
    """
    breath_rate = breaths / (duration / 60)
    return breath_rate


def count_apnea(breath_times):
    """Counts number of apnea events in data

    Iterates through the breath times and calculates time difference between
    them. If time elapsed is more than ten seconds, then it is counted as
    an apnea event

    Parameters
    ----------
    breath_times : array of floats
        All the time points at which a positive peak of a breath was recorded

    Returns
    -------
    apnea_count : integer
        Number of apnea events in data
    """
    apnea_count = 0
    for i in range(len(breath_times) - 1):
        if (breath_times[i + 1] - breath_times[i] > 10):
            apnea_count += 1
    return apnea_count


def calculate_leakage(time, flow):
    """Calculates total amount of mask leakage observed in data in liters

    Uses Scipy integrate function with Simpson's rule to approximate
    integral of area under the flow vs time curve. Multiplies by 1000 to
    convert volume from cubic meters to liters. Sign convention is that
    more flow observed going to the patient than coming back is positive.
    Logs a warning if the mask leakage is negative.

    Parameters
    ----------
    time : array of float
        Time points in seconds
    flow : array of float
        Calculated volumetric flow rates in m^3/second

    Returns
    -------
    leakage : float
        Total amount of mask leakage observed in liters
    """
    leakage = integrate.simpson(flow, time) * 1000
    if (leakage < 0):
        logging.warning("Leakage is negative")
    return leakage


def create_dictionary(duration, breaths, breath_rate_bpm, breath_times,
                      apnea_count, leakage):
    """Creates dictionary in specified format for output

    Dictionary contains keys and values of patient's duration, breaths,
    breath rate, breath times, apnea_count, and leakage.

    Parameters
    ----------
    duration : float
        Time duration of the data in seconds
    breaths : integer
        Number of breaths in the data
    breath_rate_bpm : float
        Average breathing rate from the data in breaths per minutes
    breath_times : list of floats
        Identified times for each breath
    apnea_count : integer
        Number of apnea events in the data
    leakage : float
        Total amount of mask leakage observed in the data in liters

    Returns
    -------
    metrics : dictionary
        Output dictionary containing duration, breaths,
        breath rate, breath times, apnea_count, and leakage.
    """
    metrics = {"duration": duration,
               "breaths": breaths,
               "breath_rate_bpm": breath_rate_bpm,
               "breath_times": breath_times,
               "apnea_count": apnea_count,
               "leakage": leakage}
    return metrics


def output(dictionary, number):
    """Outputs dictionary to JSON output file

    Creates file in the format "patient_NUMBER.json" then outputs
    dictionary to the file

    Parameters
    ----------
    dictionary : dictionary
        Output dictionary containing duration, breaths,
        breath rate, breath times, apnea_count, and leakage.
    number : string
        Patient's number

    Returns
    -------
    output_name : string
        Name of json file created
    """
    output_name = "patient_{}.json".format(number)
    out_file = open(output_name, "w")
    json.dump(dictionary, out_file)
    out_file.close
    return output_name


def analysis_driver(file_name):
    """Reads input file and calls on functions to process and output

    Opens the input file to be read then ignores the first line. Collects all
    time points and corresponding pressure data and checks if they are valid
    then calls on functions to convert ADC to pressure then pressure to flow.
    Analyzes time vs. flow data for breaths, apnea, and leakage then outputs
    to json file.

    Parameters
    ----------
    file_name : string
        File containing raw patient data in the currrent directory to be read

    Returns
    -------
    """
    logging.info("Start of data analysis. File Name: {}".format(file_name))
    with open(file_name, "r") as in_file:
        first_line = in_file.readline().strip("\n")
        t = np.array([])
        F = np.array([])
        for line in in_file:
            valid_line = error_check(line.strip("\n"))
            if (valid_line is False):
                continue
            data = ADC_to_Pressure(line)
            time, flow = Pressure_to_Flow(data)
            t = np.append(t, time)
            F = np.append(F, flow)
#        np.savetxt("patient0{}_times.txt".format(file_name[-5]), t)
#        np.savetxt("patient0{}_flows.txt".format(file_name[-5]), F)
        breaths, breath_times = find_breaths(t, F)
#        np.savetxt("patient0{}_breath_times.txt"
#                   .format(file_name[-5]), breath_times)
        duration = calculate_duration(t)
        breath_rate_bpm = calculate_breath_rate(duration, breaths)
        apnea_count = count_apnea(breath_times)
        leakage = calculate_leakage(t, F)
        metrics = create_dictionary(duration, breaths, breath_rate_bpm,
                                    breath_times, apnea_count, leakage)
#        output(metrics, file_name[-6:-4])
        return breath_rate_bpm, apnea_count, t, F


if __name__ == "__main__":
    logging.basicConfig(filename="log_file.log", filemode="w",
                        level=logging.INFO)
#    for i in range(8):
#        analysis_driver("sample_data/patient_0{}.txt".format(i+1))
    analysis_driver("sample_data/patient_08.txt")
