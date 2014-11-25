from applications.bootup.forms.bootupform import BOOTUPFORM

@auth.requires_login
def create():
    form=BOOTUPFORM(db.project)
    message=""
    if form.process().accepted:
        message = 'form accepted'
    elif form.errors:
        message = 'form has errors'
    return dict(form=form,message=message)

def img():
    return response.download(request, db)

def index():
    closest = db((openprojects & projectstats) & notfundedprojects).select(db.project.ALL, db.projectstat.ALL, orderby=~db.projectstat.progress, limitby=(0,5))
    newest = db((openprojects & projectstats) & notfundedprojects & includeopendate).select(db.project.ALL, db.projectstat.ALL, db.openproject.ALL, orderby=~db.openproject.opendate, limitby=(0,5))
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


def view():
    projectid = request.args(0)

    if projectid is None:
        raise HTTP(404, "Project not found")

    project = db((openprojects | closedprojects | myprojects) & projectstats & includeopendate).select(db.project.ALL,db.projectstat.ALL,db.openproject.ALL).first()
    if project is None:
        raise HTTP(404, "Project not found")

    return dict(record=project)



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

    return dict(form=form,message=message)


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


    projectopened = db(db.openproject.projectid==projectid).count()>0

    form = FORM.confirm('Open',{'Back':URL(request.env.http_referrer)})
    if form.accepted:
        if projectopened:
            db(db.closedproject.openprojectid==project.idproject).delete()
        else:
            db.openproject.insert(projectid=project.idproject)

        redirect(URL('bootup','project','view',args=[projectid]))

    return dict(project=project,form=form)

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

    form = FORM.confirm('Close',{'Back':URL(request.env.http_referrer)})
    if form.accepted:
        db.closedproject.insert(openprojectid=project.project.idproject)
        redirect(URL('bootup','project','view',args=[projectid]))

    return dict(record=project,form=form)

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

    form = FORM.confirm('Delete',{'Back':URL(request.env.http_referrer)})

    if form.accepted:
        db(db.project.idproject==projectid).delete()
        redirect('bootup','user','projects')

    return dict(project=project,form=form)

