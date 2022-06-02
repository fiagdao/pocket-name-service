from peewee import *

# will change to postgres in prod
db = SqliteDatabase('db')

class Domain(Model):
    owner = CharField(max_length=40)
    resolves_to = CharField(max_length=40)
    name = CharField(max_length=26)
    last_renewal = IntegerField(null=True) # null=True means that it is optional
    ending_date = IntegerField(null=True)
    active = BooleanField()
    parent = ForeignKeyField('self', null=True)

    class Meta:
        database=db
        db_table = "domain"

class Event(Model):
    txhash = CharField(max_length=64)
    domain = ForeignKeyField(Domain)
    old_owner = CharField(max_length=40)
    new_owner = CharField(max_length=40)
    old_resolver = CharField(max_length=40)
    new_resolver = CharField(max_length=40)
    height = IntegerField()

    class Meta:
        database = db
        db_table = "event"


class State(Model):
    height = IntegerField()

    class Meta:
        database = db
        db_table = "state"

db.create_tables([Domain, Event, State])

if State.select().count() == 0:
	State.create(height=61114)
