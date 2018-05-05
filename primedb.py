from peewee import *

primedb = SqliteDatabase('primedb.sqlite')

class BaseModel (Model):
    class Meta:
        database = primedb

class DataModel (BaseModel):
    name = CharField()

class RelationModel (BaseModel):
    pass

# Data Tables #
class ItemType (DataModel):
    pass

class Item (DataModel):
    type_ = ForeignKeyField(ItemType)

class RelicTier (DataModel):
    ordinal = SmallIntegerField()

class Relic (DataModel):
    tier = ForeignKeyField(RelicTier)
    code = CharField(max_length=2)

    @property
    def name (self):
        return "{} {}".format(self.tier.name, self.code)

class MissionSector (BaseModel):
    pass

class Mission (DataModel):
    sector = ForeignKeyField(MissionSector)


# Relation Tables #
class BuildRequirement (RelationModel):
    needs = ForeignKeyField(Item)
    build = ForeignKeyField(Item)

class Containment (RelationModel):
    contains = ForeignKeyField(Item)
    inside = ForeignKeyField(Relic)

class Drop (RelationModel):
    drops = ForeignKeyField(Relic)
    location = ForeignKeyField(Mission)


# Setup Code #
def setup_db ():
    primedb.connect()
    primedb.create_tables([ItemType, Item, RelicTier, Relic, MissionSector, Mission])

    RelicTier(name='Lith', ordinal=0).save()
    RelicTier(name='Meso', ordinal=1).save()
    RelicTier(name='Neo',  ordinal=2).save()
    RelicTier(name='Axi',  ordinal=3).save()
