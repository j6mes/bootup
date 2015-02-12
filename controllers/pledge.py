"""
Y8142984

The pledge controller is used to edit a projects pledges.
All methods are guarded by auth.requires_login.

The project/pledge is loaded from the @LoadProject and @LoadPledge decorators

The LoadPledge and LoadProject decorators are parameterised to allow access to the page to be limited for
editing/pledging
"""
w

from bootupform import BOOTUPFORM
from error import pretty_errors
from decorators import LoadPledge, LoadProject


@pretty_errors
@auth.requires_login
@LoadPledge(requires_pledge=True)
def make():
    pledge = request.vars['pledge']

    form = BOOTUPFORM.factory(db.booting)
    if form.process().accepted:
        db.booting.insert(openprojectid=pledge.project.idproject, pledgeid=pledge.pledge.idpledge,
                          addressid=form.vars.addressid,
                          cardid=form.vars.cardid, bootingdate=request.now, userid=auth.user_id)
        redirect(URL('project', 'view', args=[pledge.project.idproject]))

    return dict(pledge=pledge, form=form)


@pretty_errors
@auth.requires_login
@LoadProject(allow_preview=True, requires_edit=True)
def view():
    project = request.vars['project'].project
    return dict(project=project, projectid=project.idproject)


@pretty_errors
@auth.requires_login
@LoadProject(allow_preview=True, requires_edit=True)
def create():
    project = request.vars['project'].project

    form = BOOTUPFORM.factory(db.pledge,
                              Field('rewards', requires=IS_IN_DB(db(db.reward.projectid == project.idproject),
                                                                 db.reward.idreward, '%(description)s',
                                                                 multiple=[1, 9999],
                                                                 error_message="Please select at least one reward")))

    if ( form.process().accepted):
        pledgeid = db.pledge.insert(idpledge=None, description=form.vars.description, value=form.vars.value,
                                    projectid=project.idproject)

        """
        For each reward that was selected in the form, if the reward project matches ours, create a rewardpledge
        """
        for reward in form.vars.rewards:
            reward = int(reward)
            dbreward = db(db.reward.idreward == reward).select(db.reward.ALL).first()
            if int(dbreward.projectid) is int(project.idproject):
                db.rewardpledge.insert(rewardid=reward, pledgeid=pledgeid)

        redirect(URL('pledge', 'view', args=[project.idproject]))
    return dict(project=project, form=form, projectid=project.idproject)


@pretty_errors
@auth.requires_login
@LoadPledge(requires_edit=True)
def edit():
    pledge = request.vars['pledge']

    record = pledge.pledge
    record.rewards = pledge.pledge.rewardids()

    form = BOOTUPFORM.factory(db.pledge,
                              Field('rewards', requires=IS_IN_DB(db(db.reward.projectid == pledge.pledge.projectid),
                                                                 db.reward.idreward, '%(description)s',
                                                                 multiple=[1, 9999],
                                                                 error_message="Please select at least one reward")),
                              record=record)
    """
    As we're have to remove the rewardpledges ourselves, the simplest action is to delete all reward pledges
    then create a new set of rewardpledges for the items that the user has chosen in the form
    """
    if ( form.process().accepted):
        for reward in pledge.pledge.rewardids():
            db((db.rewardpledge.pledgeid == int(pledge.pledge.idpledge)) & (
                db.rewardpledge.rewardid == int(reward))).select(db.rewardpledge.ALL).first().rawdelete()

        for reward in form.vars.rewards:
            reward = int(reward)
            dbreward = db(db.reward.idreward == reward).select(db.reward.ALL).first()
            if int(dbreward.projectid) is int(pledge.pledge.projectid):
                db.rewardpledge.insert(rewardid=reward, pledgeid=pledge.pledge.idpledge)

        db(db.pledge.idpledge == pledge.pledge.idpledge).update(description=form.vars.description,
                                                                value=form.vars.value)

        redirect(URL('pledge', 'view', args=[pledge.pledge.projectid]))
    return dict(form=form, projectid=pledge.pledge.projectid)


@pretty_errors
@auth.requires_login
@LoadPledge(requires_edit=True)
def delete():
    pledge = request.vars['pledge']

    form = BOOTUPFORM.confirm('Delete', 'btn-danger', {'Back': URL('pledge', 'view', args=[pledge.project.idproject])})
    if form.accepted:
        db(db.pledege.idpledge == pledge.pledge.idpledge).delete()
        redirect(URL('pledge', 'view', args=[pledge.pledge.idpledge]))

    return dict(form=form)
