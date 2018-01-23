import datetime
import os
import peewee
from playhouse.db_url import connect

DB = connect(
    os.environ.get(
        'DATABASE_URL',
        'postgres://localhost:5432/project1'
    )
)

class BaseModel (peewee.Model):
    class Meta:
        database = DB

class Request (BaseModel):
    first_name = peewee.CharField(max_length=30)
    last_name = peewee.CharField(max_length=30)
    address1 = peewee.CharField(max_length=50)
    address2 = peewee.CharField(max_length=50, null=True)
    address3 = peewee.CharField(max_length=50, null=True)
    city = peewee.CharField(max_length=30)
    state = peewee.CharField(max_length=20)
    postalcode = peewee.CharField()
    latitude = peewee.FloatField()
    longitude = peewee.FloatField()
    phone = peewee.CharField()
    email = peewee.CharField()
    description = peewee.TextField()
    people_needed = peewee.IntegerField()
    truck_needed = peewee.BooleanField(default=False)
    open_request = peewee.BooleanField(default=True)
    timestamp = peewee.DateTimeField(default=datetime.datetime.utcnow)

    def __str__ (self):
        return self.name

class Volunteer (BaseModel):
    first_name = peewee.CharField(max_length=30)
    last_name = peewee.CharField(max_length=30)
    phone = peewee.CharField()
    email = peewee.CharField()
    volunteers = peewee.IntegerField()
    has_truck = peewee.BooleanField(default=False)
    timestamp = peewee.DateTimeField(default=datetime.datetime.utcnow)

    def __str__ (self):
        return self.name

class Assignment (BaseModel):
    request = peewee.ForeignKeyField(Request)
    volunteer = peewee.ForeignKeyField(Volunteer)

    def __str__ (self):
        return self.name
