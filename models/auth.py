class BootUpAuth:
    user_id = 0

    def __init__(self, db):
        self.db = db
        if session.user is None:
            self.user_id = 0
        else:
            self.user_id = session.user


    def is_logged_in(self):
        return self.user_id > 0


    def requires_login(self, fn):
        def _a(*args, **kwargs):
            if not self.is_logged_in():
                redirect(URL('bootup','user', 'login'))
                return
            return fn(*args, **kwargs)

        return _a

