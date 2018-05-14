from peewee import *

DB_PATH = 'primedb.sqlite'

_primedb = SqliteDatabase(DB_PATH)

class BaseModel (Model):
    class Meta:
        database = _primedb

class DataModel (BaseModel):
    name = CharField()

    def __str__ (self):
        return self.name

class RelationModel (BaseModel):
    pass

# Data Tables #
class ItemType (DataModel):
    pass

class Item (DataModel):
    type_ = ForeignKeyField(ItemType, backref='items')
    # ducats = IntegerField(default=0)

class RelicTier (DataModel):
    ordinal = SmallIntegerField(unique=True)

class Relic (DataModel):
    tier = ForeignKeyField(RelicTier)
    code = CharField(max_length=2)
    vaulted = BooleanField(default=False)

    class Meta:
        indexes = ((('tier', 'code'), True))

    @property
    def name (self):
        return "{} {}".format(self.tier, self.code)

# class MissionSector (BaseModel):
#     pass

# class Mission (DataModel):
#     sector = ForeignKeyField(MissionSector)


# Relation Tables #
class BuildRequirement (RelationModel):
    needs = ForeignKeyField(Item, backref='products')
    builds = ForeignKeyField(Item, backref='components')
    need_count = IntegerField(default=1)
    build_count = IntegerField(default=1)

class Containment (RelationModel):
    contains = ForeignKeyField(Item, backref='relics')
    inside = ForeignKeyField(Relic, backref='contents')

# class Drop (RelationModel):
#     drops = ForeignKeyField(Relic)
#     location = ForeignKeyField(Mission)


# Initialization Code #
def setup ():
    _primedb.create_tables([ItemType, Item, RelicTier, Relic])

    RelicTier(name='Lith', ordinal=0).save()
    RelicTier(name='Meso', ordinal=1).save()
    RelicTier(name='Neo',  ordinal=2).save()
    RelicTier(name='Axi',  ordinal=3).save()

def open ():
    needs_setup = not os.path.isfile(DB_PATH)
    _primedb.connect()
    if needs_setup: setup()

def close ():
    _primedb.close()


# Population Code #
def populate
