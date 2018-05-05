from peewee import *

primedb = SqliteDatabase('primedb.sqlite')

class BaseModel (Model):
    class Meta:
        database = primedb

class DataModel (BaseModel):
    name = CharField()

class RelationModel (BaseModel):
    pass

# Data Tables
class ItemType (DataModel):
    pass

class Item (DataModel):
    type_ = ForeignKeyField(ItemType)

class RelicTier (DataModel):
    pass

class Relic (DataModel):
    tier = ForeignKeyField(RelicTier)

class Mission (DataModel):
    pass

class Sector (BaseModel):
    pass


# Relation Tables
class BuildRequirement (BaseModel):
    needs = ForeignKeyField(Item)
    build = ForeignKeyField(Item)

class Containment (BaseModel):
    contains = ForeignKeyField(Item)
    inside = ForeignKeyField(Relic)
