from applications.bootup.modules.error import onerror

@onerror
def view():
    categoryurl = request.args(0)


    if categoryurl is None:
        raise HTTP(404,"Category not found")

    category = db(db.category.url == categoryurl).select().first()
    if category is None:
        raise HTTP(404,"Category not found")

    projects = db(searchableprojects & (db.project.categoryid == category.idcategory) &  projectstats & includeopendate).select(db.project.ALL,db.projectstat.ALL,db.openproject.ALL, orderby=db.openproject.opendate)

    return dict(category=category, projects=projects)

