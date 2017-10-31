from datetime import datetime

from bson import ObjectId
from mongoengine import *


class Port(EmbeddedDocument):
    number = IntField(required=True)
    state = BooleanField(required=True)


class Hour(EmbeddedDocument):
    start = StringField(max_length=60, required=True)  # TODO Regex here
    end = StringField(max_length=60, required=True)  # TODO Regex here


class DayHour(EmbeddedDocument):
    hour = EmbeddedDocumentField(Hour)
    days = StringField(max_length=60, required=True)


class Condition(EmbeddedDocument):
    name = StringField(required=True)
    day_hour = EmbeddedDocumentField(DayHour)
    input_port = EmbeddedDocumentField(Port)


class User(Document):
    _id = ObjectIdField(primary_key=True, default=lambda: ObjectId())
    name = StringField(max_length=120, required=True)
    last_name = StringField(max_length=120)
    email = EmailField(unique=True, required=True)
    password = StringField(min_length=8, max_length=255, required=True)
    role = StringField(max_length=120, required=True)
    _etag = StringField(max_length=120, required=True)
    created = DateTimeField()
    _updated = DateTimeField()


class Microchip(Document):
    _id = ObjectIdField(primary_key=True, default=lambda: ObjectId())
    name = StringField(max_length=60, required=True)
    description = StringField(max_length=120)
    ip = StringField(max_length=120, required=True)  # TODO Regex here
    owner = ObjectIdField(required=True, db_field='user')
    _etag = StringField(max_length=120, required=True)
    created = DateTimeField()
    _updated = DateTimeField()


class Task(Document):
    _id = ObjectIdField(primary_key=True, default=lambda: ObjectId())
    name = StringField(max_length=60)
    description = StringField(max_length=120)
    microchip = ObjectIdField(required=True)
    output_port = EmbeddedDocumentField(Port)
    conditions = EmbeddedDocumentListField(Condition)
    _etag = StringField(max_length=120, required=True)
    created = DateTimeField()
    _updated = DateTimeField()


class ReportStatus(EmbeddedDocument):
    code = StringField(required=True, max_length=60)  # TODO Change to numbers or a code
    reason = StringField(required=True, max_length=120)
    # user = ObjectIdField(required=True)  # TODO Needed?


class ReportDetails(EmbeddedDocument):
    task = ObjectIdField(required=True)
    status = EmbeddedDocumentField(ReportStatus, required=True)


class Report(Document):
    microchip = ObjectIdField(required=True)
    details = EmbeddedDocumentField(ReportDetails, required=True)
    created = DateTimeField(default=datetime.utcnow)
    _updated = DateTimeField(default=datetime.utcnow)
