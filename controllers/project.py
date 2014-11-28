from applications.bootup.forms.bootupform import BOOTUPFORM
from applications.bootup.modules.error import onerror



@auth.requires_login
def create():
    form=BOOTUPFORM(db.project)
    message=""
    if form.process().accepted:
        redirect(URL('bootup','user','projects'))
    return dict(form=form,message=message)

def img():
    return response.download(request, db)

def index():
    closest = db((openprojects & projectstats) & notfundedprojects & includeopendate & (db.user.iduser == db.project.managerid)).select(db.project.ALL, db.projectstat.ALL,db.openproject.ALL, db.user.ALL,orderby=~db.projectstat.progress, limitby=(0,6))
    newest = db((openprojects & projectstats) & notfundedprojects & includeopendate& (db.user.iduser == db.project.managerid)).select(db.project.ALL, db.projectstat.ALL, db.openproject.ALL,db.user.ALL, orderby=~db.openproject.opendate, limitby=(0,6))
    return dict(closest=closest, newest=newest)

def search():
    if(request.vars['q'] is None or len(request.vars['q'].strip())==0):
        return dict()
    else:
        q=request.vars['q'].strip()

    searchtype = (openprojects | closedprojects)
    qry = searchtype & (db.project.title.like('%'+q+'%') | (db.project.shortdescription.like('%'+q+'%'))) & projectstats
    projects = db(qry).select(db.project.ALL,db.projectstat.ALL)
    return dict(projects=projects, query=q)

@onerror
def view():
    projectid = request.args(0)

    if projectid is None:
        raise HTTP(404, "Project not found")

    preview = False
    project = db((openprojects | closedprojects) & projectstats & includeopendate & (db.user.iduser == db.project.managerid) & (db.project.idproject==projectid)).select(db.project.ALL,db.projectstat.ALL,db.openproject.ALL,db.user.ALL).first()

    if project is None:
        project=db(myprojects & projectstats & (db.user.iduser == db.project.managerid) & (db.project.idproject==projectid)).select(db.project.ALL,db.projectstat.ALL,db.user.ALL).first()
        preview=True

    if project is None:
        raise HTTP(404, "Project not found")

    return dict(record=project, preview=preview)

@onerror
@auth.requires_login
def pledge():
    projectid = request.args(0)

    if projectid is None:
        raise HTTP(404, "Project not found")

    project = db((openprojects | closedprojects | myprojects) & projectstats & includeopendate & (db.user.iduser == db.project.managerid) & (db.project.idproject==projectid)).select(db.project.ALL,db.projectstat.ALL,db.openproject.ALL,db.user.ALL).first()
    if project is None:
        raise HTTP(404, "Project not found")

    return dict(record=project)

@onerror
@auth.requires_login
def edit():
    projectid = request.args(0)

    if projectid is None:
        raise HTTP(404,"No project specified")

    project = db(myprojects & (db.project.idproject==projectid)).select(db.project.ALL).first()

    if project is None:
        raise HTTP(404,"Project not found")

    if not project.canedit():
        raise HTTP(403, "Can't edit this project")


    form=BOOTUPFORM(db.project,db(db.project.idproject==projectid).select(db.project.ALL).first(),upload=URL(img))
    message=""
    if form.process().accepted:
        redirect(URL('bootup','project','view',args=[projectid]))
    elif form.errors:
        message = 'form has errors'

    return dict(form=form,message=message,projectid=projectid)

@onerror
@auth.requires_login
def open():
    projectid = request.args(0)

    if projectid is None:
        raise HTTP(404,"No project specified")

    project = db((myprojects) & (db.project.idproject==projectid)).select(db.project.ALL).first()


    if project is None:
        raise HTTP(404,"Project not found")

    if not project.canopen():
        raise HTTP(403, "Can't open this project")

    if len(project.pledges()) == 0:
        raise HTTP(400, "Project needs pledges.")

    projectopened = db(db.openproject.projectid==projectid).count()>0

    form = BOOTUPFORM.confirm('Open','btn-primary',{'Back':URL('bootup','user','projects')})
    if form.accepted:
        if projectopened:
            db(db.closedproject.openprojectid==project.idproject).delete()
        else:
            db.openproject.insert(projectid=project.idproject)

        redirect(URL('bootup','project','view',args=[projectid]))



    return dict(project=project,form=form)

@onerror
@auth.requires_login
def close():
    projectid = request.args(0)

    if projectid is None:
        raise HTTP(404,"No project specified")

    project = db((myprojects) & (db.project.idproject==projectid) & projectstats).select(db.project.ALL,db.projectstat.ALL).first()

    if project is None:
        raise HTTP(404,"Project not found")

    if not project.project.canclose():
        raise HTTP(403, "Can't close this project")

    form = BOOTUPFORM.confirm('Close','btn-warning',{'Back':URL('bootup','user','projects')})
    if form.accepted:
        db.closedproject.insert(openprojectid=project.project.idproject)
        redirect(URL('bootup','user','projects'))

    return dict(record=project,form=form)

@onerror
@auth.requires_login
def delete():
    projectid = request.args(0)

    if projectid is None:
        raise HTTP(404,"No project specified")

    project = db((myprojects) & (db.project.idproject==projectid)).select(db.project.ALL).first()

    if project is None:
        raise HTTP(404,"Project not found")


    if not project.candelete():
        raise HTTP(403, "Can't delete this project")

    form = BOOTUPFORM.confirm('Delete','btn-danger',{'Back':URL('bootup','user','projects')})

    if form.accepted:
        db(db.project.idproject==projectid).delete()
        redirect('bootup','user','projects')

    return dict(project=project,form=form)

