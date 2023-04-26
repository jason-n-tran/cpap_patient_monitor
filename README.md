# BME 547 Final Project Sleep Lab Monitoring System
## Author:
Jason Tran

## Overview
This is a Sleep Lab Monitoring System with only the patient-side client and server/database implemented that allows patient data to be uploaded and stored on the server and for communication of updated settings to the patient.

The patient-side GUI allows for entry of patient name, medical record number, room number, CPAP pressure, and a CPAP file upload that will be analyzed for breath rate, number of apnea events, and display a flow vs. time graph which will all be uploaded to the server and stored in the database. 

## Database Format
The database is managed by mongoDB and stores patient information in the format of
```
Patient Class
{"patient_name": <patient_name>,
"patient_mrn": <medical_record_number>,
"room_number": <room_number>,
"CPAP_pressure": [<CPAP_pressure>],
"breath_rate": [<breath_rate>],
"apnea_count": [<apnea_count>],
"flow_image": [<flow_b64_string>],
"timestamp": [<datetime>]}
```
where "room_number" is the primary key and can be accessed with the "_id" key

## Video Demo link

## Server Routes
The server is deployed on `vcm-32579.vm.duke.edu:5000`

`POST /add_patient` handles both adding a new patient to the database and updating existing patients depending on whether the patient is already in the database. It takes a patient dictionary as a JSON input in the format
```
{"patient_name": <patient_name>,
"patient_mrn": <medical_record_number>,
"room_number": <room_number>,
"CPAP_pressure": <CPAP_pressure>,
"breath_rate": <breath_rate>,
"apnea_count": <apnea_count>,
"flow_image": <flow_b64_string>}
```

`GET /new_cpap_pressure/<room_number>/<new_value>` adds an updated CPAP pressure to the cpap_pressure_updates dictionary in the format 
```
{<room_number> : <new_value>}
```

`GET /CPAP_query/<room_number>` obtains any updated CPAP pressure value from the cpap_pressure_updates dictionary for the specified room number

## GUI Instructions
Initially running the GUI with the terminal command line `python patient_GUI.py` will open a window with boxes to type in numberical values for the patient's name, medical record number, room number, and CPAP pressure. A medical record number and room number must be entered at the minimum before clicking the upload button which will send the information to the server and a pop-up window will confirm that the information has been uploaded and whether a new patient was created or an existing patient was updated. If one of these are not entered, there will be an error pop up message indicating which one needs to be entered. After the first time uploading information, the entry boxes for medical record number and room number will be grayed out and the data will be locked in so that they cannot be changed and any subsequent uploads will only be for that medical record number and room number and the only changes that can be made are to the name, cpap pressure, and cpap calculated data. If you want to upload data for a different room number or change the medical record number, you must click the reset button which will clear all data and allow for a fresh upload.