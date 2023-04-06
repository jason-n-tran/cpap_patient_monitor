import tkinter as tk
from tkinter import ttk
from tkinter import filedialog as fd
from PIL import Image, ImageTk


def requirements_met(mrn, room_number):
    if (mrn == ""):
        return "Missing Patient Medical Record Number", False
    elif (room_number == ""):
        return "Missing Room Number", False
    else:
        return "Information Uploaded", True


def validate_pressure(pressure):
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


def query_server():
    return


def set_up_window():

    def ok_btn_cmd():
        print("Ok clicked")
        mrn = mrn_value.get()
        room_number = room_value.get()
        msg, met = requirements_met(mrn, room_number)
        if (met):
            patient_name = name_value.get()
            pressure = pressure_value.get()
            msg, valid_pressure = validate_pressure(pressure)
            if (valid_pressure):
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

    def cancel_btn_cmd():
        root.destroy()

    root = tk.Tk()
    root.title("Patient GUI")
    root.geometry("800x800")

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

    msg_label = ttk.Label(root, text="")
    msg_label.grid(column=1, row=5, columnspan=10)

    ok_button = ttk.Button(root, text="Upload", command=ok_btn_cmd)
    ok_button.grid(column=1, row=6)
    cancel_button = ttk.Button(root, text="Cancel", command=cancel_btn_cmd)
    cancel_button.grid(column=2, row=6)

    root.after(30000, query_server)

    root.mainloop()


if __name__ == "__main__":
    set_up_window()
