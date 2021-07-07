from flask_admin import Admin,BaseView,expose,AdminIndexView
class AdminPage(AdminIndexView):
    @expose('/')
    def index(self):
        return self.render('AstroAdmin.html',log=False) #панель администратора
    def is_accessible(self):
        try:
            return current_user.id==1
        except:
            return abort(403)
    def inaccessible_callback(self, name, **kwargs):
        return abort(403)

class AdminView(BaseView):
    def is_accessible(self):
        return User.query.get(current_user.id).role=='admin'
    def inaccessible_callback(self, **kwargs):
        return abort(403)

class adding(AdminView): #добавление записи
    @expose('/')
    def add(self):
        return self.render('NewArticle.html',log=False,
                           admin=[i.id for i in User.query.filter_by(role='admin').all()])

class new_tag(AdminView): #добавление тега
    @expose('/')
    def add(self):
        return self.render('NewTag.html',log=False,
                           admin=[i.id for i in User.query.filter_by(role='admin').all()])
