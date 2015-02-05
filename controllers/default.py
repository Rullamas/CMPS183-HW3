import logging
from datetime import datetime

# Main Function
def index():
    # Title of page is reached at request.args(0)
    title = request.args(0) or 'main page'
    # Redirect to main page
    if title == 'main page':
        redirect(URL('default', 'index', args = [title]))

    form = None
    content = None
    
    # Taken from Luca's code
    newpost = request.vars.newpost == 'true'
    editing = request.vars.edit == 'true'
    content = ''
    
    # Required for assignment
    edit_button = False

    # Let's uppernice the title.  The last 'title()' below
    # is actually a Python function, if you are wondering.
    display_title = title.title()

    # Selecting the most recent revision
    page = db(db.pagetable.name == title).select().first()
    # Assigning the proper ID address
    page_id = page.id if page is not None else '' 

    # Executed if no page currently exists. Taken from @163 on Piazza
    if page is None: 
        content = SQLFORM.confirm('Create new page?')
        if content.accepted:
            redirect(URL('default', 'index', args=[title], vars=dict(newpost='true')))
    # Executed if revisions exist and can be edited
    else:
        rev = db(db.revision.page_id == page.id).select(orderby=~db.revision.date_posted).first()
        # Below was originally not working, but Rakshit helped to fix
        content = represent_wiki(rev.body)
        edit_button = True

    # Process for developing a new wiki page, very similar to developing a revision
    if newpost:
        form = SQLFORM.factory(Field('body', 'text',
                                     label='Content',
                                     ))
        form.add_button('Cancel', URL('default', 'index', args=[title]))
        if form.process().accepted:
            if page is None:
                
                ############################################################################
                #
                # Originally, content being set equal to rev.body was not returning a string
                # resulting in an error when trying to compile the app. This was due to not
                # properly inserting information into the revision, as originally the code was
                # 'db.pagetable.insert(name=title)'. By assigning page_id to the code just
                # mentioned, you properly establish the content to the ID of the page being
                # worked on and save it for later use.
                #
                ############################################################################
                
                page_id=db.pagetable.insert(name=title)
                db.revision.insert(body=form.vars.body, page_id=page_id)
            redirect(URL('default', 'index', args=[title]))
        content = form
    
    # Process for developing a revision, very similar to developing a new wiki page
    # Help was received from Rakshit Agrawal, the TA for CMPS 183
    if editing:
        rev = db(db.revision.page_id == page.id).select(orderby=~db.revision.date_posted).first()
        form = SQLFORM.factory(Field('body', 'text',
                                     label='Content',
                                     default= rev.body,
                                     ))
        form.add_button('Cancel', URL('default', 'index', args=[title]))
        if form.process().accepted:
            db.revision.insert(body=form.vars.body, page_id=page.id)
            redirect(URL('default', 'index', args=[title]))
        content = form

    # Return the title, content, declaration of the state of the page (newpost), and functionality to edit to the index view
    return dict(display_title=display_title, content=content, title=title,  newpost=newpost, edit_button=edit_button)


def user():
    """
    exposes:
    http://..../[app]/default/user/login
    http://..../[app]/default/user/logout
    http://..../[app]/default/user/register
    http://..../[app]/default/user/profile
    http://..../[app]/default/user/retrieve_password
    http://..../[app]/default/user/change_password
    http://..../[app]/default/user/manage_users (requires membership in
    use @auth.requires_login()
        @auth.requires_membership('group name')
        @auth.requires_permission('read','table name',record_id)
    to decorate functions that need access control
    """
    return dict(form=auth())


@cache.action()
def download():
    """
    allows downloading of uploaded files
    http://..../[app]/default/download/[filename]
    """
    return response.download(request, db)


def call():
    """
    exposes services. for example:
    http://..../[app]/default/call/jsonrpc
    decorate with @services.jsonrpc the functions to expose
    supports xml, json, xmlrpc, jsonrpc, amfrpc, rss, csv
    """
    return service()


@auth.requires_login()
def api():
    """
    this is example of API with access control
    WEB2PY provides Hypermedia API (Collection+JSON) Experimental
    """
    from gluon.contrib.hypermedia import Collection
    rules = {
        '<tablename>': {'GET':{},'POST':{},'PUT':{},'DELETE':{}},
        }
    return Collection(db).process(request,response,rules)
