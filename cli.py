import primedb as db

def get_yn (prompt="Yes or No?"):
    yn = input("{} (y/n):  ".format(prompt))
    while not yn in ('Y', 'y', 'N', 'n'):
        yn = input("Please enter 'y' or 'n':  ")

def initialize_collection ():
    for product in db.Item.select_products():
        requirements = (db.BuildRequirement.select()
                      .where(db.BuildRequirement.builds==product))

        owned = get_yn("Do you have {}?".format(product))

        if owned in 'Nn':
            product.needed = 1
            for req in requirements:
                component = req.needs
                comp_owned = input("Enter # of owned {}:  ".format(component))
                while True:
                    try:
                        comp_owned = int(comp_owned)
                        if comp_owned < 0: raise ValueError("Must be positive")
                        break # TODO rewrite w/o break
                    except ValueError (e):
                        comp_owned = input("Please enter a positive number:  ")
                
