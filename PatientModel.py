from pymodm import MongoModel, fields


class Patient(MongoModel):
    patient_mrn = fields.IntegerField(primary_key=True)
    room_number = fields.IntegerField()
    patient_name = fields.CharField()
    CPAP_pressure = fields.ListField()
    breath_rate = fields.ListField()
    apnea_count = fields.ListField()
    flow_image: fields.ListField()
