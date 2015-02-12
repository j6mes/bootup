from gluon import current,redirect, URL, HTTP
import hashlib, os
class BootUpAuth:
    user_id = 0


    def __init__(self):
        if current.session.user is None:
            self.user_id = 0
        else:
            self.user_id = current.session.user




    def is_logged_in(self):
        return self.user_id > 0


    def requires_login(self,fn):
        def _a(*args, **kwargs):
            if not self.is_logged_in():
                redirect(URL('user', 'login'))
                return
            return fn(*args, **kwargs)

        return _a

    def logout(self):
        current.session.user = 0

    def exists(self,username):
        return current.db(current.db.user.username.like(username)).count>0

    def generate_hash(self,salt,password):
        return hashlib.sha256(hashlib.sha256(password).hexdigest() + salt).hexdigest()

    def authenticate(self,username, password):
        user = current.db((current.db.credential.userid == current.db.user.iduser) & (current.db.user.username.like(username))).select(
            current.db.user.iduser, current.db.credential.passwordsalt, current.db.credential.passwordhash).first()

        if user is None:
            return False

        if self.generate_hash(user.credential.passwordsalt,password) == user.credential.passwordhash:
            current.session.user = user.user.iduser
            return True
        else:
            return False

    def user_authenticate(self, password):
        credential = current.db(current.db.credential.userid == self.user_id).select(current.db.credential.passwordsalt, current.db.credential.passwordhash).first()

        if self.generate_hash(credential.passwordsalt,password) == credential.passwordhash:
            return True
        else:
            return False

    def set_password(self, password):
        salt = os.urandom(12).encode('base_64')
        hash = self.generate_hash(salt,password)

        current.db(current.db.credential.userid==self.user_id).update(passwordhash=hash,passwordsalt=salt)


    def force_integrity(self):
        if self.user_id >0:
            if current.request.controller not in ['address','card','user']:
                addresses = current.db(current.db.address.userid==self.user_id).count()
                if addresses == 0:
                    redirect(URL("address","create", args=['register']))

                cards = current.db(current.db.card.userid==self.user_id).count()
                if cards == 0:
                    redirect(URL("card","register"))