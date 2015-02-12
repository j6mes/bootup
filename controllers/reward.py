"""
Y8142984

The reward controller is used to edit a projects rweards.
All methods are guarded by auth.requires_login.

The project/reward is loaded from the @LoadProject and @loadreward decorators

Like the pledge view, the LoadProject decorators are parameterised to allow access to the page to be limited for
editing/pledging
"""

from bootupform import BOOTUPFORM
from error import pretty_errors
from decorators import LoadProject, loadreward


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

    form = BOOTUPFORM.factory(db.reward)
    if ( form.process().accepted):
        db.reward.insert(description=form.vars.description, projectid=project.idproject)
        redirect(URL('reward', 'view', args=[project.idproject]))
    return dict(project=project, form=form, projectid=project.idproject)


@pretty_errors
@auth.requires_login
@loadreward
def edit():
    reward = request.vars['reward']

    form = BOOTUPFORM(db.reward, record=reward.reward)
    if ( form.process().accepted):
        redirect(URL('reward', 'view', args=[reward.reward.projectid]))
    return dict(form=form, projectid=reward.reward.projectid)


@pretty_errors
@auth.requires_login
@loadreward
def delete():
    reward = request.vars['reward']

    form = BOOTUPFORM.confirm('Delete', 'btn-danger', {'Back': URL('pledge', 'view', args=[reward.project.idproject])})

    projectid = reward.reward.projectid

    if form.accepted:
        reward.reward.rawdelete()
        redirect(URL('reward', 'view', args=[projectid]))

    return dict(form=form, projectid=projectid)
