from peewee import *
from bs4 import BeautifulSoup, SoupStrainer
import urllib3

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

class Rarity (DataModel):
    ordinal = SmallIntegerField(unique=True)

class Relic (DataModel):
    tier = ForeignKeyField(RelicTier)
    code = CharField(max_length=2)
    vaulted = BooleanField(default=False)

    class Meta:
        indexes = ( (('tier', 'code'), True), )

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
    rarity = ForeignKeyField(Rarity)

# class Drop (RelationModel):
#     drops = ForeignKeyField(Relic)
#     location = ForeignKeyField(Mission)


# Initialization Code #
def setup ():
    _primedb.create_tables([ItemType, Item, RelicTier, Relic, Rarity,
                            BuildRequirement, Containment])

    RelicTier(name='Lith', ordinal=0).save()
    RelicTier(name='Meso', ordinal=1).save()
    RelicTier(name='Neo',  ordinal=2).save()
    RelicTier(name='Axi',  ordinal=3).save()

    Rarity(name='Common', ordinal=0).save()
    Rarity(name='Uncommon', ordinal=1).save()
    Rarity(name='Rare', ordinal=2).save()

def open_ ():
    needs_setup = not os.path.isfile(DB_PATH)
    _primedb.connect()
    if needs_setup: setup()

def close ():
    _primedb.close()


# Population Code #
def populate ():
    http = urllib3.PoolManager()
    r = http.request('GET', 'http://warframe.wikia.com/wiki/Void_Relic/ByRewards/SimpleTable')
    tablerows = BeautifulSoup(r.data, parse_only=SoupStrainer('tr'))

    tier_records={}
    for tier in RelicTier.select():
        tier_records[tier.name] = tier

    for row in tablerows.contents[2:]:
        contents = row.contents
        product = contents[1].text.strip()
        part = contents[2].text.strip()
        name = product + ' ' + part
        relic_tier = tier_records[contents[3].text.strip()]
        relic_code = contents[4].text.strip()
        

    return tablerows

open_()
rows = populate()
close()
