# warframe-primetracker
Database to track Prime acquisition in Warframe. This program will probably remain
abandoned, as I haven't played Warframe regularly in years.

## Use
Use instructions are given for a *nix environment, because I'm a fool who plays
Warframe on Linux.

### GUI
```
$ ./primetrackerapp.py
```

Currently, the GUI can only be used to populate the database and establish an
initial inventory of prime parts. Modifying or querying the inventory must be
done through the command line.

### Command Line
```
$ python3 -i primedb.py
```

The classes in primedb.py that represent the database tables have an assortment
of virtual properties that can provide some limited imformation. Refer to the
[peewee docs](http://docs.peewee-orm.com/en/latest/peewee/querying.html) for
information about how to write queries.

## Dependencies
- [python3 (>3.7.2)](https://www.python.org/downloads/)
- [peewee (>3.8.2)](http://docs.peewee-orm.com/en/latest/peewee/installation.html)
- [BeautifulSoup4 (>4.7.1)](https://www.crummy.com/software/BeautifulSoup/#Download)
- [certifi (>2018.11.29)](https://github.com/certifi/python-certifi)
- [kivy (>1.10.1)](https://kivy.org/#download)

The versions listed after each dependency are what I used while devloping this
tool. Newer versions will probably work, but older versions may not.
