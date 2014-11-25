import hashlib,os

from applications.bootup.forms.bootupform import BOOTUPFORM


class REGISTRATIONFORM(BOOTUPFORM):
    @staticmethod
    def factory():
        return REGISTRATIONFORM(
            DAL(None).define_table('user', db.user, Field('password',type="password"),
            Field('confirmpassword',type='password',label="Confirm Password", requires=IS_EQUAL_TO(request.vars.password, error_message="Passwords do not match")),
            db.address))


    def insertuserinfo(self,form):
        user = db.user.insert(**db.user._filter_fields(form.vars))
        form.vars.userid = user['iduser']

        db.address.insert(**db.address._filter_fields(form.vars))

        credentialvars =dict()
        credentialvars['userid'] = user['iduser']
        credentialvars['passwordsalt'] = os.urandom(12).encode('base_64')
        credentialvars['passwordhash'] = hashlib.sha256(hashlib.sha256(form.vars.password).hexdigest() + credentialvars['passwordsalt']).hexdigest()
        db.credential.update_or_insert(**credentialvars)


    def process(self,**kwargs):
        return super(REGISTRATIONFORM,self).process(onvalidation=self.insertuserinfo,**kwargs)



class LOGINFORM(BOOTUPFORM):
    def checkuser(self,form):
        user = db((db.credential.userid==db.user.iduser) & (db.user.username.like(form.vars.username))).select(db.user.iduser,db.credential.passwordsalt,db.credential.passwordhash).first()
        if user is None:
            form.errors.username = "User is not registered"
        elif hashlib.sha256(hashlib.sha256(form.vars.password).hexdigest() + user.credential.passwordsalt).hexdigest() != user.credential.passwordhash:
            form.errors.password = "Incorrect password"
        else:
            session.user = user.user.iduser


    def process(self,**kwargs):
        return super(LOGINFORM,self).process(onvalidation=self.checkuser,**kwargs)

    @staticmethod
    def factory(**kwargs):
        return LOGINFORM(DAL(None).define_table("no_table",
                Field('username'),
                Field('password', type='password')
        ), **kwargs)



def register():
    form=REGISTRATIONFORM.factory()


    message=""

    if form.process().accepted:
        message = 'form accepted'
    elif form.errors:
        message = 'form has errors'
    return dict(form=form,message=message)

def login():
    form=LOGINFORM.factory()


    if form.process().accepted:
        redirect(URL('bootup','user','index'))

    return dict(form=form)

@auth.requires_login
def logout():
    session.user = 0
    redirect(URL('bootup','project','index'))


@auth.requires_login
def index():
    projects = db(db.user.iduser == auth.user_id).select().first().expectedrewards()
    return dict(projects=projects)



@auth.requires_login
def projects():
    qry = myprojects

    if(request.args(0)=="not_started"):
        qry &= notstartedprojects
    elif(request.args(0)=="opened"):
        qry &= openprojects
    elif(request.args(0)=="not_funded"):
        qry &= closedprojects & notfundedprojects
    elif(request.args(0)=="funded"):
        qry &= closedprojects & fundedprojects

    projects = db(qry & projectstats).select(db.project.ALL,db.projectstat.ALL)
    return dict(projects=projects)