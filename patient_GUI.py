import tkinter as tk
from tkinter import ttk
from tkinter import filedialog as fd
# from PIL import Image, ImageTk
from cpap_measurements import analysis_driver
import matplotlib
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import requests
import io
import base64
import random

server = "http://127.0.0.1:5000"
# server = "http://vcm-32579.vm.duke.edu:5000"
cpap_calculated = False


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


def display_all_patients():
    """
    Displays all patients from database in a new window
    This function makes a GET request to the server to retrieve all patient
    records and displays them in a new scrollable window. Each patient's
    information is shown including their room number, MRN, name, and all
    recorded CPAP data with timestamps.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    try:
        r = requests.get(server + "/get_all_patients")
        if r.status_code != 200:
            tk.messagebox.showerror(
                title="Error",
                message="Failed to retrieve patients: {}".format(r.text)
            )
            return

        patients = r.json()

        # Create new window
        display_window = tk.Toplevel()
        display_window.title("All Patients - Monitoring View")
        display_window.geometry("1200x800")
        display_window.configure(bg="#f0f4f8")

        # Create header
        header_frame = tk.Frame(display_window, bg="#2c3e50")
        header_frame.pack(fill=tk.X, pady=(0, 20))
        header_label = tk.Label(
            header_frame,
            text="All Patients Database View",
            font=(
                'Helvetica',
                20,
                'bold'),
            bg="#2c3e50",
            fg="#ffffff",
            pady=15)
        header_label.pack()

        # Create scrollable frame
        canvas = tk.Canvas(display_window, bg="#f0f4f8")
        scrollbar = tk.Scrollbar(
            display_window,
            orient="vertical",
            command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#f0f4f8")

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        if len(patients) == 0:
            no_patients_label = tk.Label(scrollable_frame,
                                         text="No patients in database",
                                         font=('Helvetica', 14),
                                         bg="#f0f4f8", fg="#2c3e50")
            no_patients_label.pack(pady=50)
        else:
            # Display each patient
            for idx, patient in enumerate(patients):
                patient_frame = tk.Frame(scrollable_frame, bg="#ffffff",
                                         relief=tk.RAISED, borderwidth=2)
                patient_frame.pack(fill=tk.X, padx=20, pady=10)

                # Patient header
                header_text = "Room {} - {} (MRN: {})".format(
                    patient['room_number'],
                    patient['patient_name'],
                    patient['patient_mrn']
                )
                patient_header = tk.Label(patient_frame, text=header_text,
                                          font=('Helvetica', 12, 'bold'),
                                          bg="#3498db", fg="#ffffff", pady=8)
                patient_header.pack(fill=tk.X)

                # Patient details frame
                details_frame = tk.Frame(patient_frame, bg="#ffffff")
                details_frame.pack(fill=tk.BOTH, padx=15, pady=10)

                # Display CPAP data if available
                if len(patient['CPAP_pressure']) > 0:
                    data_label = tk.Label(
                        details_frame,
                        text="CPAP Data Records: {}".format(
                            len(patient['CPAP_pressure'])
                        ),
                        font=('Helvetica', 10, 'bold'),
                        bg="#ffffff",
                        fg="#2c3e50",
                        anchor=tk.W
                    )
                    data_label.pack(fill=tk.X, pady=(0, 5))

                    # Create table-like display
                    for i in range(len(patient['CPAP_pressure'])):
                        record_frame = tk.Frame(
                            details_frame, bg="#f0f4f8",
                            relief=tk.GROOVE, borderwidth=1
                        )
                        record_frame.pack(fill=tk.X, pady=2)

                        t_val = (patient['timestamp'][i]
                                 if i < len(patient['timestamp']) else "N/A")
                        br_val = (patient['breath_rate'][i]
                                  if i < len(patient['breath_rate']) else 0)
                        ap_val = (patient['apnea_count'][i]
                                  if i < len(patient['apnea_count']) else 0)

                        record_text = (
                            "  [{}/{}] Time: {} | CPAP Pressure: {} cmH2O | "
                            "Breath Rate: {:.2f} breaths/min | "
                            "Apnea Events: {}"
                        ).format(
                            i + 1,
                            len(patient['CPAP_pressure']),
                            t_val,
                            patient['CPAP_pressure'][i],
                            br_val,
                            ap_val
                        )

                        # Highlight if apnea count >= 2
                        fg_color = "#e74c3c" if (
                            i < len(patient['apnea_count']) and
                            patient['apnea_count'][i] >= 2
                        ) else "#2c3e50"

                        record_label = tk.Label(record_frame, text=record_text,
                                                font=('Helvetica', 9),
                                                bg="#f0f4f8", fg=fg_color,
                                                anchor=tk.W, justify=tk.LEFT)
                        record_label.pack(fill=tk.X, padx=5, pady=3)
                else:
                    no_data_label = tk.Label(details_frame,
                                             text="No CPAP data recorded yet",
                                             font=('Helvetica', 10, 'italic'),
                                             bg="#ffffff", fg="#95a5a6")
                    no_data_label.pack(pady=5)

        canvas.pack(side="left", fill="both", expand=True, padx=10)
        scrollbar.pack(side="right", fill="y")

        # Close button
        close_button = tk.Button(display_window, text="Close",
                                 command=display_window.destroy,
                                 bg="#95a5a6", fg="#ffffff",
                                 font=('Helvetica', 12, 'bold'),
                                 relief=tk.RAISED, borderwidth=3,
                                 padx=30, pady=10)
        close_button.pack(pady=15)

    except Exception as e:
        tk.messagebox.showerror(
            title="Error",
            message="Failed to display patients: {}".format(
                str(e)))


def set_up_window():

    fig = Figure(figsize=(14, 6))
    global cpap_calculated
    cpap_calculated = False

    # Color scheme
    BG_COLOR = "#f0f4f8"
    HEADER_BG = "#2c3e50"
    HEADER_FG = "#ffffff"
    FRAME_BG = "#ffffff"
    ACCENT_COLOR = "#3498db"
    BUTTON_BG = "#3498db"
    BUTTON_FG = "#ffffff"
    RESET_BG = "#95a5a6"
    LABEL_FG = "#2c3e50"

    def ok_btn_cmd():
        """
        Uploads entered data to server
        This function performs the data validation and GUI changes when the
        user requests to upload entered information to the server. It retrieves
        values from entry fields and validates them and displays a messagebox
        indicating the problem if there is an error in validation or success
        when the data is uploaded. It deactivates the MRN and room number entry
        boxes while allowing the rest to be changed for future uploads. This
        function also sends a get request to the /new_cpap_pressure/
        <room_number>/<pressure> route if new CPAP calculated data has been
        selected from a data file to randomly update the pressure to a value
        between 4 and 25 inclusive.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        global cpap_calculated
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
                tk.messagebox.showinfo(title="Success", message=r.text)
                mrn_entry.configure(state=tk.DISABLED)
                room_entry.configure(state=tk.DISABLED)
                if (cpap_calculated):
                    s = requests.get(server + "/new_cpap_pressure/{}/{}"
                                     .format(room_number, random.randint(4, 25)
                                             ))
                    print(s.status_code)
                    print(s.text)
                    root.after(30000, query_server)
                    cpap_calculated = False
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
        global cpap_calculated
        cpap_calculated = True
        filename = fd.askopenfilename()
        if (filename != ""):
            tk.messagebox.showinfo(title="File Selected", message=filename)
            breath_rate, apnea_count, time, flow = analysis_driver(filename)
            breathrate_value.configure(text=str(breath_rate))
            if (apnea_count >= 2):
                # Create custom style for alert
                style.configure(
                    'Alert.TLabel',
                    font=(
                        'Helvetica',
                        10,
                        'bold'),
                    background=FRAME_BG,
                    foreground='#e74c3c',
                    padding=5)
                apnea_value.configure(
                    text=str(apnea_count), style='Alert.TLabel')
            else:
                apnea_value.configure(
                    text=str(apnea_count), style='Value.TLabel')

            # Create graph frame with styling
            graph_frame = tk.Frame(
                scrollable_frame,
                bg=FRAME_BG,
                relief=tk.RAISED,
                borderwidth=2)
            graph_frame.grid(column=0, row=3, columnspan=100, sticky='ew',
                             padx=20, pady=10)

            graph_title = ttk.Label(
                graph_frame,
                text="CPAP Flow Rate Analysis",
                style='Section.TLabel')
            graph_title.pack(pady=(10, 5))

            a = fig.add_subplot(111)
            a.clear()
            a.plot(time, flow, color=ACCENT_COLOR, linewidth=1.5)
            a.set_xlabel('Time (seconds)', fontsize=11, fontweight='bold')
            a.set_ylabel(
                'Flow (cubic meters per second)',
                fontsize=11,
                fontweight='bold')
            a.grid(True, alpha=0.3)
            canvas = FigureCanvasTkAgg(fig, graph_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(padx=15, pady=(5, 15))

    def query_server():
        """
        Queries server for CPAP pressure updates
        This function checks that the GUI has valid mrn and room numbers
        entered before making a get request to the server every 30 seconds to
        the /CPAP_query/<room_number> route which returns any new CPAP pressure
        values for the specified room number. If there is an update, the GUI's
        CPAP pressure entry box will be changed to display the new number.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        mrn = mrn_value.get()
        room_number = room_value.get()
        msg, met = requirements_met(mrn, room_number)
        if (met):
            r = requests.get(server + "/CPAP_query/{}".format(room_number))
            print(r.status_code)
            print("New CPAP pressure of {} found for room number {}"
                  .format(r.text, room_number))
            if (r.status_code == 200):
                pressure_entry.delete(0, tk.END)
                pressure_entry.insert(0, "{}".format(r.text))
                a = pressure_entry.get()
                a = a[:-1]
                pressure_entry.delete(0, tk.END)
                pressure_entry.insert(0, a)
        root.after(30000, query_server)

    root = tk.Tk()
    root.title("Sleep Lab Patient Monitoring System")
    root.geometry("1600x1000")
    root.configure(bg=BG_COLOR)

    # Configure style for ttk widgets
    style = ttk.Style()
    style.theme_use('clam')
    style.configure('Header.TLabel', font=('Helvetica', 24, 'bold'),
                    background=HEADER_BG, foreground=HEADER_FG, padding=15)
    style.configure('Section.TLabel', font=('Helvetica', 12, 'bold'),
                    background=FRAME_BG, foreground=ACCENT_COLOR, padding=5)
    style.configure('Info.TLabel', font=('Helvetica', 10),
                    background=FRAME_BG, foreground=LABEL_FG, padding=5)
    style.configure('Value.TLabel', font=('Helvetica', 10, 'bold'),
                    background=FRAME_BG, foreground=ACCENT_COLOR, padding=5)
    style.configure('Custom.TEntry', font=('Helvetica', 10), padding=5)
    style.configure('Custom.TButton', font=('Helvetica', 10, 'bold'),
                    padding=10)

    # Create main container with scrollbar
    main_container = tk.Frame(root, bg=BG_COLOR)
    main_container.pack(fill=tk.BOTH, expand=True)

    # Create canvas and scrollbar
    canvas = tk.Canvas(main_container, bg=BG_COLOR)
    scrollbar = tk.Scrollbar(
        main_container,
        orient="vertical",
        command=canvas.yview)
    scrollable_frame = tk.Frame(canvas, bg=BG_COLOR)

    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    # Enable mouse wheel scrolling
    def on_mousewheel(event):
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    canvas.bind_all("<MouseWheel>", on_mousewheel)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # Header
    header_frame = tk.Frame(scrollable_frame, bg=HEADER_BG)
    header_frame.grid(
        column=0,
        row=0,
        columnspan=100,
        sticky='ew',
        pady=(
            0,
            20))
    top_label = ttk.Label(
        header_frame,
        text="Sleep Lab Patient Monitoring System",
        style='Header.TLabel')
    top_label.pack(pady=10)

    # Patient Information Frame
    patient_frame = tk.Frame(
        scrollable_frame,
        bg=FRAME_BG,
        relief=tk.RAISED,
        borderwidth=2)
    patient_frame.grid(column=0, row=1, columnspan=100, sticky='ew',
                       padx=20, pady=10)

    patient_title = ttk.Label(patient_frame, text="Patient Information",
                              style='Section.TLabel')
    patient_title.grid(
        column=0,
        row=0,
        columnspan=2,
        pady=(
            10,
            15),
        sticky=tk.W,
        padx=15)

    name_label = ttk.Label(patient_frame, text="Name:", style='Info.TLabel')
    name_label.grid(column=0, row=1, sticky=tk.E, padx=(15, 5), pady=5)
    name_value = tk.StringVar()
    name_entry = ttk.Entry(patient_frame, textvariable=name_value, width=30,
                           style='Custom.TEntry', font=('Helvetica', 10))
    name_entry.grid(column=1, row=1, padx=(5, 15), pady=5, sticky=tk.W)

    mrn_label = ttk.Label(patient_frame, text="Medical Record Number:",
                          style='Info.TLabel')
    mrn_label.grid(column=0, row=2, sticky=tk.E, padx=(15, 5), pady=5)
    mrn_value = tk.StringVar()
    mrn_entry = ttk.Entry(patient_frame, textvariable=mrn_value, width=30,
                          style='Custom.TEntry', font=('Helvetica', 10))
    mrn_entry.grid(column=1, row=2, padx=(5, 15), pady=5, sticky=tk.W)

    room_label = ttk.Label(patient_frame, text="Room Number:",
                           style='Info.TLabel')
    room_label.grid(column=0, row=3, sticky=tk.E, padx=(15, 5), pady=5)
    room_value = tk.StringVar()
    room_entry = ttk.Entry(patient_frame, textvariable=room_value, width=30,
                           style='Custom.TEntry', font=('Helvetica', 10))
    room_entry.grid(column=1, row=3, padx=(5, 15), pady=5, sticky=tk.W)

    pressure_label = ttk.Label(patient_frame, text="CPAP Pressure (cmH2O):",
                               style='Info.TLabel')
    pressure_label.grid(column=0, row=4, sticky=tk.E, padx=(15, 5), pady=5)
    pressure_value = tk.StringVar()
    pressure_entry = ttk.Entry(
        patient_frame,
        textvariable=pressure_value,
        width=30,
        style='Custom.TEntry',
        font=(
            'Helvetica',
            10))
    pressure_entry.grid(
        column=1, row=4, padx=(
            5, 15), pady=(
            5, 15), sticky=tk.W)

    # CPAP Data Frame
    cpap_frame = tk.Frame(
        scrollable_frame,
        bg=FRAME_BG,
        relief=tk.RAISED,
        borderwidth=2)
    cpap_frame.grid(column=0, row=2, columnspan=100, sticky='ew',
                    padx=20, pady=10)

    cpap_title = ttk.Label(cpap_frame, text="CPAP Data Analysis",
                           style='Section.TLabel')
    cpap_title.grid(column=0, row=0, columnspan=2, pady=(10, 15), sticky=tk.W,
                    padx=15)

    choose_file_button = tk.Button(
        cpap_frame,
        text="Select CPAP Data File",
        command=display_CPAP,
        bg=ACCENT_COLOR,
        fg=BUTTON_FG,
        font=(
            'Helvetica',
            10,
            'bold'),
        relief=tk.RAISED,
        borderwidth=2,
        padx=20,
        pady=8,
        cursor='hand2')
    choose_file_button.grid(column=0, row=1, columnspan=2, pady=10, padx=15)

    breathrate_label = ttk.Label(
        cpap_frame,
        text="Breathing Rate (breaths/min):",
        style='Info.TLabel')
    breathrate_label.grid(column=0, row=2, sticky=tk.E, padx=(15, 5), pady=5)
    breathrate_value = ttk.Label(cpap_frame, text="Not measured",
                                 style='Value.TLabel')
    breathrate_value.grid(column=1, row=2, sticky=tk.W, padx=(5, 15), pady=5)

    apnea_label = ttk.Label(cpap_frame, text="Number of Apnea Events:",
                            style='Info.TLabel')
    apnea_label.grid(column=0, row=3, sticky=tk.E, padx=(15, 5), pady=(5, 15))
    apnea_value = ttk.Label(
        cpap_frame,
        text="Not measured",
        style='Value.TLabel')
    apnea_value.grid(column=1, row=3, sticky=tk.W, padx=(5, 15), pady=(5, 15))

    # Action Buttons Frame
    button_frame = tk.Frame(scrollable_frame, bg=BG_COLOR)
    button_frame.grid(column=0, row=50, columnspan=100, pady=20)

    ok_button = tk.Button(
        button_frame,
        text="Upload to Server",
        command=ok_btn_cmd,
        bg=BUTTON_BG,
        fg=BUTTON_FG,
        font=(
            'Helvetica',
            12,
            'bold'),
        relief=tk.RAISED,
        borderwidth=3,
        padx=30,
        pady=12,
        cursor='hand2')
    ok_button.grid(column=0, row=0, padx=10)

    reset_button = tk.Button(
        button_frame,
        text="Reset Form",
        command=reset_btn_cmd,
        bg=RESET_BG,
        fg=BUTTON_FG,
        font=(
            'Helvetica',
            12,
            'bold'),
        relief=tk.RAISED,
        borderwidth=3,
        padx=30,
        pady=12,
        cursor='hand2')
    reset_button.grid(column=1, row=0, padx=10)

    view_all_button = tk.Button(
        button_frame,
        text="View All Patients",
        command=display_all_patients,
        bg="#27ae60",
        fg=BUTTON_FG,
        font=(
            'Helvetica',
            12,
            'bold'),
        relief=tk.RAISED,
        borderwidth=3,
        padx=30,
        pady=12,
        cursor='hand2')
    view_all_button.grid(column=2, row=0, padx=10)

    # Status message
    msg_label = tk.Label(
        scrollable_frame,
        text="",
        font=(
            'Helvetica',
            10,
            'italic'),
        bg=BG_COLOR,
        fg=LABEL_FG)
    msg_label.grid(column=0, row=51, columnspan=100, pady=10)

    root.mainloop()


if __name__ == "__main__":
    set_up_window()
