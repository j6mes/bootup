import hashlib
import os
from datetime import datetime,date

from bootupform import BOOTUPFORM
from gluon.sqlhtml import Field
from gluon import DAL, current, redirect, URL
from gluon.validators import IS_LENGTH, IS_EQUAL_TO, IS_IN_DB

from gluon import H3,DIV
from applications.bootup.models.db import auth

def label_widget(field, value):
    return DIV(H3(field.name))


def computebirthdate(form):
    form.vars.dateofbirth = date(int(form.vars.dateofbirth_year), int(form.vars.dateofbirth_month),int(form.vars.dateofbirth_day))



class REGISTRATIONFORM(BOOTUPFORM):
    @staticmethod
    def factory():
        return REGISTRATIONFORM(
            DAL(None).define_table('user',
                                   Field('Your Details',label='' ,required=False,widget=label_widget),

                                   current.db.user,



                                   Field('password', type="password",
                                          requires=IS_LENGTH(minsize=6, error_message="Password must be at least 6 characters long")),
                                   Field('confirmpassword', type='password', label="Confirm Password",
                                        requires=IS_EQUAL_TO(current.request.vars.password,
                                                              error_message="Passwords do not match")),
                                   Field('Shipping Address',label='', required= False,widget=label_widget),
                                   current.db.address))

    def insertuserinfo(self, form):
        computebirthdate(form)
        user = current.db.user.insert(**current.db.user._filter_fields(form.vars))
        form.vars.userid = user['iduser']

        current.db.address.insert(**current.db.address._filter_fields(form.vars))

        credentialvars = dict()
        credentialvars['userid'] = user['iduser']
        credentialvars['passwordsalt'] = os.urandom(12).encode('base_64')
        credentialvars['passwordhash'] = hashlib.sha256(
            hashlib.sha256(form.vars.password).hexdigest() + credentialvars['passwordsalt']).hexdigest()
        current.db.credential.update_or_insert(**credentialvars)

        current.session.user = user['iduser']
        redirect(URL('card','register'))

    def process(self, **kwargs):
        return super(REGISTRATIONFORM, self).process(onvalidation=self.insertuserinfo, **kwargs)


class LOGINFORM(BOOTUPFORM):
    def login(self, form):
        exists = auth.exists(form.vars.username)

        if not exists:
            form.errors.username = "User is not registered"
            return

        authenticated = auth.authenticate(form.vars.username, form.vars.password)

        if not authenticated:
            form.errors.password = "Incorrect password"
            return

    def process(self, **kwargs):
        return super(LOGINFORM, self).process(onvalidation=self.login, **kwargs)

    @staticmethod
    def factory(**kwargs):
        return LOGINFORM(DAL(None).define_table("no_table",
                                                Field('username'),
                                                Field('password', type='password')
        ), **kwargs)




class CHANGEPASSWORDFORM(BOOTUPFORM):
    def change(self, form):
        if not auth.user_authenticate(form.vars.oldpassword):
            form.errors.oldpassword = "Incorrect password"
            return

        auth.set_password(form.vars.password)
        redirect(URL('user','index'))

    def process(self, **kwargs):
        return super(CHANGEPASSWORDFORM, self).process(onvalidation=self.change, **kwargs)

    @staticmethod
    def factory(**kwargs):
        return CHANGEPASSWORDFORM(DAL(None).define_table("no_table",
                                                Field('oldpassword',type='password',label="Old Password"),
                                                Field('password', type='password',label="New Password",requires=IS_LENGTH(minsize=6, error_message="Password must be at least 6 characters long")),
                                                Field('confirmpassword',type='password',label="Confirm Password",requires=IS_EQUAL_TO(current.request.vars.password,
                                                              error_message="Passwords do not match"))
        ), **kwargs)





def label_widget(field, value):
    return DIV(H3(field.name))


def computedate(form):
    form.vars.expdate = date(int(str(current.request.now.year)[0:2] + form.vars.expdate_year), int(form.vars.expdate_month),
                             current.calendar.monthrange(int(str(current.request.now.year)[0:2] + form.vars.expdate_year),
                                                 int(form.vars.expdate_month))[1])


class CARDREGISTERFORM(BOOTUPFORM):
    def __init__(self, *args, **kwargs):
        self.redirect_url = kwargs['redirect_url']
        super(CARDREGISTERFORM, self).__init__(*args, **kwargs)


    def setupaddr(self, form):
        if form.errors.addressid is not None:
            if ( form.errors.street is not None and
                         form.errors.city is not None and
                         form.errors.postcode is not None and
                         form.errors.countrycode is not None):
                del form.errors.addressid
                form.vars.addressid = 0
        else:
            if form.errors.street is not None:
                del form.errors.street

            if form.errors.city is not None:
                del form.errors.city

            if form.errors.postcode is not None:
                del form.errors.postcode

            if form.errors.countrycode is not None:
                del form.errors.countrycode

        if form.errors.number is None and form.errors.expdate is None and form.errors.pin is None and form.vars.expdate_month is not None and form.vars.expdate_year is not None:
            self.register(form)

    def register(self, form):
        computedate(form)

        if len(form.vars.addressid) is 0:
            form.vars.addressid = current.db.address.insert(**current.db.address._filter_fields(form.vars))

        form.vars.userid = auth.user_id
        current.db.card.insert(**current.db.card._filter_fields(form.vars))
        redirect(self.redirect_url)

    def process(self, **kwargs):
        return super(CARDREGISTERFORM, self).process(
            onvalidation={'onfailure': self.setupaddr, 'onsuccess': self.register}, **kwargs)

    @staticmethod
    def factory(**kwargs):
        return CARDREGISTERFORM(DAL(None).define_table("no_table",
                                                       Field('Credit Card', label='', required=False,
                                                             widget=label_widget),
                                                       current.db.card.number,
                                                       current.db.card.expdate,
                                                       current.db.card.pin,
                                                       Field('Billing Address', label='', required=False,
                                                             widget=label_widget),
                                                       Field('addressid', type='reference address',
                                                             label='Billing Address',
                                                             requires=IS_IN_DB(current.db(current.db.address.userid == auth.user_id),
                                                                               current.db.address.idaddress,
                                                                               '%(street)s, %(city)s, %(postcode)s',
                                                                               zero='Set up new billing address',
                                                                               error_message='Please choose your billing address'
                                                             )),
                                                       db.address

        ), **kwargs)

