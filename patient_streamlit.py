import streamlit as st
import requests
import io
import base64
import time
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import random
import os
from cpap_measurements import analysis_driver

# Server configuration - use environment variable or default to localhost
SERVER = os.environ.get("API_URL", "http://127.0.0.1:5000")
# For Duke VM deployment, set API_URL to: http://vcm-32579.vm.duke.edu:5000

# Page configuration
st.set_page_config(
    page_title="Sleep Lab Patient Monitoring System",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main {
        padding: 0rem 1rem;
    }
    .stAlert {
        margin-top: 1rem;
    }
    h1 {
        color: #2c3e50;
        padding: 1rem 0;
    }
    h2 {
        color: #3498db;
        padding: 0.5rem 0;
    }
    .metric-card {
        background-color: #f0f4f8;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 2px solid #3498db;
    }
    .alert-metric {
        background-color: #ffe6e6;
        border-color: #e74c3c;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'patient_locked' not in st.session_state:
    st.session_state.patient_locked = False
if 'cpap_data' not in st.session_state:
    st.session_state.cpap_data = None
if 'last_poll_time' not in st.session_state:
    st.session_state.last_poll_time = 0
if 'mrn' not in st.session_state:
    st.session_state.mrn = ""
if 'room_number' not in st.session_state:
    st.session_state.room_number = ""
if 'patient_name' not in st.session_state:
    st.session_state.patient_name = ""
if 'cpap_pressure' not in st.session_state:
    st.session_state.cpap_pressure = ""


def validate_pressure(pressure):
    """
    Validates entered CPAP pressure

    Parameters
    ----------
    pressure : string
        entry for CPAP pressure in units of cmH2O

    Returns
    -------
    tuple
        (message, is_valid)
    """
    if pressure == "":
        return "Information Uploaded", True
    try:
        pressure_int = int(pressure)
        if 4 <= pressure_int <= 25:
            return "Information Uploaded", True
        else:
            return "CPAP Pressure is not between 4 and 25", False
    except ValueError:
        return "CPAP pressure is not an integer", False


def plot_to_b64(fig):
    """
    Converts matplotlib figure to base64 encoded string

    Parameters
    ----------
    fig : matplotlib figure
        figure containing CPAP time vs. flow chart

    Returns
    -------
    string
        base64 encoded string of image
    """
    my_stringIObytes = io.BytesIO()
    fig.savefig(my_stringIObytes, format='jpg')
    my_stringIObytes.seek(0)
    my_base64_jpgData = base64.b64encode(my_stringIObytes.read())
    b64_string = str(my_base64_jpgData, encoding='utf-8')
    return b64_string


def create_json(mrn, room, name, pressure, rate, apnea, image):
    """
    Creates dictionary of patient information

    Parameters
    ----------
    mrn : int or string
        patient's medical record number
    room : int or string
        patient's room number
    name : string
        patient's name
    pressure : int or string
        patient's entered CPAP pressure
    rate : float or string
        patient's breathing rate as calculated from file
    apnea : int or string
        number of apnea events in CPAP data
    image : string
        base64 encoded string of CPAP flow vs. time plot

    Returns
    -------
    dict
        dictionary containing patient information
    """
    patient = {
        "patient_name": name,
        "patient_mrn": mrn,
        "room_number": room,
        "CPAP_pressure": pressure,
        "breath_rate": rate,
        "apnea_count": apnea,
        "flow_image": image
    }
    return patient


def query_server_for_pressure(room_number):
    """
    Queries server for CPAP pressure updates

    Parameters
    ----------
    room_number : string
        patient's room number

    Returns
    -------
    string or None
        new CPAP pressure value if available
    """
    try:
        r = requests.get(f"{SERVER}/CPAP_query/{room_number}", timeout=5)
        if r.status_code == 200:
            # Remove trailing newline if present
            pressure = r.text.strip()
            return pressure
    except Exception as e:
        st.sidebar.error(f"Error querying server: {e}")
    return None


def upload_to_server(mrn, room_number, patient_name, cpap_pressure, cpap_data):
    """
    Uploads patient data to server

    Parameters
    ----------
    mrn : string
        medical record number
    room_number : string
        room number
    patient_name : string
        patient name
    cpap_pressure : string
        CPAP pressure value
    cpap_data : dict or None
        CPAP analysis results

    Returns
    -------
    tuple
        (success: bool, message: string)
    """
    # Validate required fields
    if not mrn:
        return False, "Missing Patient Medical Record Number"
    if not room_number:
        return False, "Missing Room Number"

    # Validate pressure
    msg, valid = validate_pressure(cpap_pressure)
    if not valid:
        return False, msg

    # Prepare data
    if cpap_data:
        breath_rate = cpap_data['breath_rate']
        apnea_count = cpap_data['apnea_count']
        image = cpap_data['image_b64']
    else:
        breath_rate = "Not measured"
        apnea_count = "Not measured"
        # Create empty plot
        fig = Figure(figsize=(10, 4))
        image = plot_to_b64(fig)

    # Create patient data
    patient = create_json(
        int(mrn), int(room_number), patient_name,
        cpap_pressure, breath_rate, apnea_count, image
    )

    try:
        r = requests.post(f"{SERVER}/add_patient", json=patient, timeout=10)
        if r.status_code == 200:
            # If CPAP data was uploaded, trigger random pressure update
            if cpap_data:
                new_pressure = random.randint(4, 25)
                requests.get(
                    f"{SERVER}/new_cpap_pressure/{room_number}/{new_pressure}",
                    timeout=5
                )
            return True, r.text
        else:
            return False, f"Server error: {r.text}"
    except Exception as e:
        return False, f"Connection error: {str(e)}"


def get_all_patients():
    """
    Retrieves all patients from server

    Returns
    -------
    tuple
        (success: bool, data: list or error_message: string)
    """
    try:
        r = requests.get(f"{SERVER}/get_all_patients", timeout=10)
        if r.status_code == 200:
            return True, r.json()
        else:
            return False, f"Failed to retrieve patients: {r.text}"
    except Exception as e:
        return False, f"Connection error: {str(e)}"


def process_cpap_file(uploaded_file):
    """
    Processes uploaded CPAP data file

    Parameters
    ----------
    uploaded_file : UploadedFile
        Streamlit uploaded file object

    Returns
    -------
    dict or None
        Dictionary with breath_rate, apnea_count, time, flow, image_b64
    """
    import os
    import traceback

    temp_path = None
    try:
        # Save uploaded file temporarily
        temp_path = f"temp_cpap_{int(time.time())}.csv"
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        # Analyze the file
        breath_rate, apnea_count, time_data, flow_data = analysis_driver(
            temp_path)

        # Create plot
        fig = Figure(figsize=(12, 5))
        ax = fig.add_subplot(111)
        ax.plot(time_data, flow_data, color='#3498db', linewidth=1.5)
        ax.set_xlabel('Time (seconds)', fontsize=11, fontweight='bold')
        ax.set_ylabel(
            'Flow (cubic meters per second)',
            fontsize=11,
            fontweight='bold')
        ax.set_title('CPAP Flow Rate Analysis', fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3)

        # Convert to base64
        image_b64 = plot_to_b64(fig)

        # Clean up temp file
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)

        return {
            'breath_rate': breath_rate,
            'apnea_count': apnea_count,
            'time': time_data,
            'flow': flow_data,
            'image_b64': image_b64,
            'fig': fig
        }
    except Exception as e:
        # Clean up temp file on error
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except BaseException:
                pass
        st.error(f"Error processing CPAP file: {str(e)}")
        st.error(f"Traceback: {traceback.format_exc()}")
        return None


def reset_form():
    """Resets the form to initial state"""
    st.session_state.patient_locked = False
    st.session_state.cpap_data = None
    st.session_state.last_processed_file = None
    st.session_state.mrn = ""
    st.session_state.room_number = ""
    st.session_state.patient_name = ""
    st.session_state.cpap_pressure = ""
    st.rerun()


# Main App
def main():
    st.title("🏥 Sleep Lab Patient Monitoring System")

    # Sidebar for auto-refresh and actions
    with st.sidebar:
        st.header("⚙️ Settings")

        # Auto-refresh toggle for server polling
        auto_refresh = st.checkbox("Auto-refresh CPAP Pressure", value=True)
        if auto_refresh:
            refresh_interval = st.slider(
                "Refresh interval (seconds)", 10, 60, 30)

            # Check if it's time to poll
            current_time = time.time()
            if (current_time - st.session_state.last_poll_time >
                    refresh_interval):
                if st.session_state.room_number:
                    new_pressure = query_server_for_pressure(
                        st.session_state.room_number)
                    if (new_pressure and
                            new_pressure != st.session_state.cpap_pressure):
                        st.session_state.cpap_pressure = new_pressure
                        st.sidebar.success(
                            f"🔄 Updated pressure: {new_pressure} cmH2O")
                st.session_state.last_poll_time = current_time
                time.sleep(0.1)
                st.rerun()

        st.divider()

        # Reset button
        if st.button("🔄 Reset Form", use_container_width=True):
            reset_form()

        st.divider()
        st.caption(f"Server: {SERVER}")

    # Main content tabs
    tab1, tab2 = st.tabs(["📋 Patient Data Entry", "👥 View All Patients"])

    with tab1:
        # Patient Information Section
        st.header("Patient Information")

        col1, col2 = st.columns(2)

        with col1:
            patient_name = st.text_input(
                "Patient Name",
                value=st.session_state.patient_name,
                key="name_input"
            )
            st.session_state.patient_name = patient_name

            mrn = st.text_input(
                "Medical Record Number (MRN)*",
                value=st.session_state.mrn,
                disabled=st.session_state.patient_locked,
                key="mrn_input",
                help="Required field"
            )
            if not st.session_state.patient_locked:
                st.session_state.mrn = mrn

        with col2:
            room_number = st.text_input(
                "Room Number*",
                value=st.session_state.room_number,
                disabled=st.session_state.patient_locked,
                key="room_input",
                help="Required field"
            )
            if not st.session_state.patient_locked:
                st.session_state.room_number = room_number

            cpap_pressure = st.text_input(
                "CPAP Pressure (cmH2O)",
                value=st.session_state.cpap_pressure,
                key="pressure_input",
                help="Must be an integer between 4 and 25"
            )
            st.session_state.cpap_pressure = cpap_pressure

        st.divider()

        # CPAP Data Analysis Section
        st.header("CPAP Data Analysis")

        # Add option to use sample data or upload file
        data_source = st.radio(
            "Select data source:",
            ["Use Sample Data", "Upload Your Own File"],
            horizontal=True,
            key="data_source_radio"
        )

        uploaded_file = None
        selected_sample = None

        if data_source == "Use Sample Data":
            # Get list of sample files
            sample_dir = "sample_data"
            if os.path.exists(sample_dir):
                sample_files = [f for f in os.listdir(
                    sample_dir) if f.endswith('.txt')]
                sample_files.sort()

                if sample_files:
                    selected_sample = st.selectbox(
                        "Select a sample patient file:",
                        sample_files,
                        key="sample_file_selector"
                    )

                    if selected_sample:
                        st.info(f"📁 Selected: {selected_sample}")
                else:
                    st.warning("No sample files found in sample_data folder")
            else:
                st.warning("sample_data folder not found")
        else:
            uploaded_file = st.file_uploader(
                "Upload CPAP Data File",
                type=['csv', 'txt'],
                help="Select a CPAP data file for analysis",
                key="cpap_file_uploader"
            )

        # Track if we've processed this specific file
        if 'last_processed_file' not in st.session_state:
            st.session_state.last_processed_file = None

        # Process button for sample files
        if selected_sample and data_source == "Use Sample Data":
            if st.button("📊 Load Sample Data", use_container_width=True):
                sample_path = os.path.join("sample_data", selected_sample)
                file_id = selected_sample + str(os.path.getsize(sample_path))

                if st.session_state.last_processed_file != file_id:
                    with st.spinner("Processing CPAP data..."):
                        # Use analysis_driver directly on the sample file
                        try:
                            (breath_rate, apnea_count,
                             time_data, flow_data) = analysis_driver(
                                sample_path)

                            # Create plot
                            fig = Figure(figsize=(12, 5))
                            ax = fig.add_subplot(111)
                            ax.plot(
                                time_data,
                                flow_data,
                                color='#3498db',
                                linewidth=1.5)
                            ax.set_xlabel(
                                'Time (seconds)',
                                fontsize=11, fontweight='bold')
                            ax.set_ylabel(
                                'Flow (cubic meters per second)',
                                fontsize=11,
                                fontweight='bold')
                            ax.set_title(
                                'CPAP Flow Rate Analysis',
                                fontsize=12,
                                fontweight='bold')
                            ax.grid(True, alpha=0.3)

                            # Convert to base64
                            image_b64 = plot_to_b64(fig)

                            cpap_data = {
                                'breath_rate': breath_rate,
                                'apnea_count': apnea_count,
                                'time': time_data,
                                'flow': flow_data,
                                'image_b64': image_b64,
                                'fig': fig
                            }

                            st.session_state.cpap_data = cpap_data
                            st.session_state.last_processed_file = file_id
                            st.success(f"✅ File processed: {selected_sample}")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error processing sample file: {str(e)}")
                else:
                    st.info("This file has already been loaded")

        # Process uploaded files
        if uploaded_file is not None:
            # Check if this is a new file or the same file
            file_id = uploaded_file.name + str(uploaded_file.size)

            if st.session_state.last_processed_file != file_id:
                with st.spinner("Processing CPAP data..."):
                    cpap_data = process_cpap_file(uploaded_file)
                    if cpap_data:
                        st.session_state.cpap_data = cpap_data
                        st.session_state.last_processed_file = file_id
                        st.success(f"✅ File processed: {uploaded_file.name}")
                        st.rerun()
                    else:
                        st.error("Failed to process CPAP data file")
            else:
                # File already processed, just show it was loaded
                st.info(f"📁 Current file: {uploaded_file.name}")

        # Display CPAP analysis results
        if st.session_state.cpap_data:
            col1, col2 = st.columns(2)

            with col1:
                br = st.session_state.cpap_data['breath_rate']
                st.metric(
                    label="Breathing Rate",
                    value=f"{br:.2f} breaths/min"
                )

            with col2:
                apnea_count = st.session_state.cpap_data['apnea_count']
                if apnea_count >= 2:
                    st.markdown(
                        '<div class="metric-card alert-metric">\n'
                        '<h3 style="color: #e74c3c; margin: 0;">'
                        '⚠️ Apnea Events</h3>\n'
                        '<h2 style="color: #e74c3c; margin: 0.5rem 0 0 0;">'
                        f'{apnea_count}</h2>\n</div>',
                        unsafe_allow_html=True
                    )
                else:
                    st.metric(label="Apnea Events", value=apnea_count)

            # Display the flow rate chart
            st.subheader("CPAP Flow Rate Over Time")
            st.pyplot(st.session_state.cpap_data['fig'])
        else:
            col1, col2 = st.columns(2)
            with col1:
                st.info("Breathing Rate: Not measured")
            with col2:
                st.info("Apnea Events: Not measured")

        st.divider()

        # Upload button
        if st.button(
            "📤 Upload to Server",
            type="primary",
                use_container_width=True):
            with st.spinner("Uploading data..."):
                success, message = upload_to_server(
                    st.session_state.mrn,
                    st.session_state.room_number,
                    st.session_state.patient_name,
                    st.session_state.cpap_pressure,
                    st.session_state.cpap_data
                )

                if success:
                    st.success(f"✅ {message}")
                    st.session_state.patient_locked = True
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(f"❌ {message}")

    with tab2:
        st.header("All Patients Database View")

        if st.button("🔄 Refresh Patient List", use_container_width=True):
            st.rerun()

        with st.spinner("Loading patients..."):
            success, data = get_all_patients()

        if success:
            patients = data

            if len(patients) == 0:
                st.info("No patients in database")
            else:
                # Display patient count
                st.success(f"Found {len(patients)} patient(s) in database")

                # Display each patient
                for idx, patient in enumerate(patients):
                    with st.expander(
                        f"🏥 Room {patient['room_number']} - "
                        f"{patient['patient_name']} "
                        f"(MRN: {patient['patient_mrn']})",
                        expanded=False
                    ):
                        # Display patient details
                        if len(patient.get('CPAP_pressure', [])) > 0:
                            st.write(
                                "**CPAP Data Records:** "
                                f"{len(patient['CPAP_pressure'])}")

                            # Create a dataframe for better display
                            records = []
                            for i in range(len(patient['CPAP_pressure'])):
                                tstmp = patient.get('timestamp', [])
                                t_val = tstmp[i] if i < len(tstmp) else "N/A"
                                br = patient.get('breath_rate', [])
                                br_val = f"{br[i]:.2f}" if i < len(br) else "0"
                                ac = patient.get('apnea_count', [])
                                ac_val = ac[i] if i < len(ac) else 0
                                rec_str = (f"{i + 1}/"
                                           f"{len(patient['CPAP_pressure'])}")
                                cpap_val = patient['CPAP_pressure'][i]
                                record = {
                                    "Record": rec_str,
                                    "Timestamp": t_val,
                                    "CPAP Pressure (cmH2O)": cpap_val,
                                    "Breath Rate (breaths/min)": br_val,
                                    "Apnea Events": ac_val
                                }
                                records.append(record)

                            # Display as table
                            import pandas as pd
                            df = pd.DataFrame(records)

                            # Highlight rows with apnea >= 2
                            def highlight_apnea(row):
                                if row['Apnea Events'] >= 2:
                                    return [
                                        'background-color: #ffe6e6'] * len(row)
                                return [''] * len(row)

                            styled_df = df.style.apply(highlight_apnea, axis=1)
                            st.dataframe(
                                styled_df, use_container_width=True,
                                hide_index=True)
                        else:
                            st.info("No CPAP data recorded yet")
        else:
            st.error(f"❌ {data}")


if __name__ == "__main__":
    main()
