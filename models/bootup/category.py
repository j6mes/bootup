class Category():
    @staticmethod
    def all():
        return db().select(db.category.ALL)


    @staticmethod
    def where(query):
        return db(query).select(db.category.ALL)