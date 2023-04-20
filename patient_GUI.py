import tkinter as tk
from tkinter import ttk
from tkinter import filedialog as fd
from PIL import Image, ImageTk
from cpap_measurements import analysis_driver
import matplotlib
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import requests
import io
import base64


server = "http://127.0.0.1:5000"


def requirements_met(mrn, room_number):
    """
    Checks for entered patient MRN and room number
    This function performs the data validation when the user tries to upload
    information to ensure that they have entered in a value for the medical
    record number and room number by checking that they are not empty strings
    then returns a message indicating which field is missing if any and a
    boolean indicating whether the requirements have been met.

    Parameters
    ----------
    mrn : string
        entry for patient medical record number
    room_number : string
        entry for patient room number

    Returns
    -------
    string
        message indicating which field is missing
    boolean
        False if requirements haven't been met, True if they have
    """
    if (mrn == ""):
        return "Missing Patient Medical Record Number", False
    elif (room_number == ""):
        return "Missing Room Number", False
    else:
        return "Information Uploaded", True


def validate_pressure(pressure):
    """
    Validates entered CPAP pressure
    This function performs the data validation when the user tries to upload
    a CPAP pressure value. It passes if no pressure value is entered but
    otherwise checks that the value entered is a valid integer and is
    between 4 and 25 inclusive. It returns a message indicating what the
    problem is and a boolean indicating whether the pressure is valid.

    Parameters
    ----------
    pressure : string
        entry for CPAP pressure in units of cmH2O

    Returns
    -------
    string
        message indicating problem with CPAP pressure value
    boolean
        False if CPAP pressure entry is invalid, True if valid
    """
    if (pressure == ""):
        return "Information Uploaded", True
    else:
        try:
            int(pressure)
        except ValueError:
            return "CPAP pressure is not an integer", False
        else:
            if 4 <= int(pressure) <= 25:
                return "Information Uploaded", True
            else:
                return "CPAP Pressure is not between 4 and 25", False


def plot_to_b64(fig):
    """
    Converts matplotlib figure to base64 encoded string
    This function takes a matplotlib figure object and saves it to an IO
    buffer in jpg format. It then uses base64 encoding to convert the image to
    base64 and finally formats it as a string to be sent in json serialization.

    Parameters
    ----------
    fig : matplotlib figure
        figure containing CPAP time vs. flow chart

    Returns
    -------
    b64_string : string
        base64 encoded string of image
    """
    my_stringIObytes = io.BytesIO()
    fig.savefig(my_stringIObytes, format='jpg')
    my_stringIObytes.seek(0)
    my_base64_jpgData = base64.b64encode(my_stringIObytes.read())
    b64_string = str(my_base64_jpgData, encoding='utf-8')
    # image_bytes = base64.b64decode(my_base64_jpgData)
    # image_buf = io.BytesIO(image_bytes)
    # i = matplotlib.image.imread(image_buf, format='JPG')
    # matplotlib.pyplot.imshow(i, interpolation='nearest')
    # matplotlib.pyplot.show()
    return b64_string


def create_json(mrn, room, name, pressure, rate, apnea, image):
    """
    Creates dictionary of patient information
    This function takes the information entered from the patient GUI and
    formats it into a dictionary to be sent with json later. The dictionary is
    formatted as
        patient = {"patient_name": <patient_name>,
                    "patient_mrn": <medical_record_number>,
                    "room_number": <room_number>,
                    "CPAP_pressure": <CPAP_pressure>,
                    "breath_rate": <breath_rate>,
                    "apnea_count": <apnea_count>,
                    "flow_image": <flow_b64_string>}

    Parameters
    ----------
    mrn : integer or string
        patient's medical record number
    room : integer or string
        patient's room number
    name : string
        patient's name
    pressure : integer or string
        patient's entered CPAP pressure
    rate : float or string
        patient's breathing rate as calculated from file
    apnea : integer or string
        number of apnea events in CPAP data
    image : string
        base64 encoded string of CPAP flow vs. time plot

    Returns
    -------
    patient : dictionary
        dictionary containing entries formatted as specified above
    """
    patient = {"patient_name": name,
               "patient_mrn": mrn,
               "room_number": room,
               "CPAP_pressure": pressure,
               "breath_rate": rate,
               "apnea_count": apnea,
               "flow_image": image}
    return patient


def query_server():
    return


def set_up_window():

    fig = Figure(figsize=(14, 6))

    def ok_btn_cmd():
        """
        Uploads entered data to server
        This function performs the data validation and GUI changes when the
        user requests to upload entered information to the server. It retrieves
        values from entry fields and validates them and displays a messagebox
        indicating the problem if there is an error in validation or success
        when the data is uploaded. It deactivates the MRN and room number entry
        boxes while allowing the rest to be changed for future uploads.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        print("Ok clicked")
        mrn = mrn_value.get()
        room_number = room_value.get()
        msg, met = requirements_met(mrn, room_number)
        if (met):
            patient_name = name_value.get()
            pressure = pressure_value.get()
            msg, valid_pressure = validate_pressure(pressure)
            if (valid_pressure):
                breath_rate = breathrate_value.cget("text")
                apnea_count = apnea_value.cget("text")
                image = plot_to_b64(fig)
                patient = create_json(int(mrn), int(room_number), patient_name,
                                      pressure, breath_rate, apnea_count,
                                      image)
                r = requests.post(server + "/add_patient", json=patient)
                print(r.status_code)
                print(r.text)
                msg_label.configure(text=msg)
                tk.messagebox.showinfo(title="Success", message=msg)
                mrn_entry.configure(state=tk.DISABLED)
                room_entry.configure(state=tk.DISABLED)
            else:
                msg_label.configure(text=msg)
                tk.messagebox.showerror(title="Error", message=msg)
        else:
            msg_label.configure(text=msg)
            tk.messagebox.showerror(title="Error", message=msg)

    def reset_btn_cmd():
        """
        Resets GUI
        This function destroys the ttk root which effectively closes the
        patient side graphical user interface before rerunning the
        set_up_window function to open the GUI with a clean slate. Any entries
        and displayed data are removed and grayed out boxes are available for
        new entries and data about the previous patient is removed.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        root.destroy()
        set_up_window()

    def display_CPAP():
        """
        Processes uploaded CPAP data
        This function allows the user to select a CPAP data file from their
        local computer and analyzes it for the breathing rate, number of apnea
        events, and flow rate vs. time. The breathing rate and number of apnea
        events are displayed on the GUI while the flow rate vs. time is plotted
        as a graph. If there are two or more apnea events, the value is
        displayed as red to indicate an alert.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        filename = fd.askopenfilename()
        tk.messagebox.showinfo(title="File Selected", message=filename)
        breath_rate, apnea_count, time, flow = analysis_driver(filename)
        breathrate_value.configure(text=breath_rate)
        if (apnea_count >= 2):
            apnea_value.configure(text=apnea_count, foreground="red")
        else:
            apnea_value.configure(text=apnea_count, foreground="black")
        a = fig.add_subplot(111)
        a.plot(time, flow)
        a.set_xlabel('Time (seconds)')
        a.set_ylabel('Flow (cubic meters per second)')
        canvas = FigureCanvasTkAgg(fig, root)
        canvas.draw()
        canvas.get_tk_widget().grid(column=0, row=8, columnspan=100)

    root = tk.Tk()
    root.title("Patient GUI")
    root.geometry("1600x1000")

    top_label = ttk.Label(root, text="Patient GUI")
    top_label.grid(column=0, row=0, columnspan=2, sticky=tk.W)

    name_label = ttk.Label(root, text="Name:")
    name_label.grid(column=0, row=1, sticky=tk.E)
    name_value = tk.StringVar()
    name_entry = ttk.Entry(root, textvariable=name_value)
    name_entry.grid(column=1, row=1, padx=5)

    mrn_label = ttk.Label(root, text="Medical Record Number:")
    mrn_label.grid(column=0, row=2, sticky=tk.E)
    mrn_value = tk.StringVar()
    mrn_entry = ttk.Entry(root, textvariable=mrn_value)
    mrn_entry.grid(column=1, row=2, padx=5)

    room_label = ttk.Label(root, text="Room Number:")
    room_label.grid(column=0, row=3, sticky=tk.E)
    room_value = tk.StringVar()
    room_entry = ttk.Entry(root, textvariable=room_value)
    room_entry.grid(column=1, row=3, padx=5)

    pressure_label = ttk.Label(root, text="CPAP Pressure:")
    pressure_label.grid(column=0, row=4, sticky=tk.E)
    pressure_value = tk.StringVar()
    pressure_entry = ttk.Entry(root, textvariable=pressure_value)
    pressure_entry.grid(column=1, row=4, padx=5)

    choose_file_button = ttk.Button(root, text="Select CPAP data file",
                                    command=display_CPAP)
    choose_file_button.grid(column=1, row=5)

    breathrate_label = ttk.Label(root, text="Breathing rate "
                                 "(breaths per minute):")
    breathrate_label.grid(column=0, row=6, sticky=tk.E)
    breathrate_value = ttk.Label(root, text="")
    breathrate_value.grid(column=1, row=6, sticky=tk.W)

    apnea_label = ttk.Label(root, text="Number of apnea events:")
    apnea_label.grid(column=0, row=7, sticky=tk.E)
    apnea_value = ttk.Label(root, text="")
    apnea_value.grid(column=1, row=7, sticky=tk.W)

    msg_label = ttk.Label(root, text="")
    msg_label.grid(column=1, row=50, columnspan=10)

    ok_button = ttk.Button(root, text="Upload", command=ok_btn_cmd)
    ok_button.grid(column=1, row=51)
    reset_button = ttk.Button(root, text="Reset", command=reset_btn_cmd)
    reset_button.grid(column=2, row=51)

    root.after(30000, query_server)

    root.mainloop()


if __name__ == "__main__":
    set_up_window()
