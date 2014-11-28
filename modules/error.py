from gluon import HTTP,LOAD,current


def onerror(function):
  def _a(*args,**kwargs):
    try:
        return function(*args,**kwargs)
    except HTTP, e:
        ctx=dict(a='b')
        e.body= current.response.render('error/view.html',msg=e.body)
        raise e
  return _a
