from gluon import HTTP, LOAD, current



def includemenu(function):
    def _a(*args, **kwargs):
        result = function(*args, **kwargs)
        result['categories'] = current.db().select(current.db.category.ALL)
        return result

    return _a
