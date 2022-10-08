import os
from .utilities import filesIO, now, never
from .utilities import decorate_class, debugger, logger


class Project():

    ACTIVE = 'active'
    COMPLETED = 'completed'

    todolist = None
    
    def __init__(self, name):
        self.name = name
        self.iname = int(name)
        self.status = Project.ACTIVE
        self.path = os.path.join(Project.todolist.path, name + '.project')
        self.info = self.read()
        self.urgency = 0

        self.write() 


    def _newborn_info(self):
        return {
            'description': '',
            'importance': 100,
            'due': never(),
            'created': now()
        }


    def __str__(self):
        return f'<Project {self.name}>'


    def __repr__(self):
        return f'<Project {self.name}>'


    def read(self):
        if os.path.isfile(self.path):
            info = filesIO.read(self.path, loads=True)
        else:
            info = self._newborn_info()
        return info


    def write(self):
        filesIO.write(self.path, self.info, dumps=True)
        

    @property
    def following(self):
        return self.info['following']
        
    @following.setter
    def following(self, value):
        self.info['following'] = value
        self.write()


    @property
    def followers(self):
        return self.info['followers']
        
    @followers.setter
    def followers(self, value):
        self.info['followers'] = value
        self.write()

    
    @property
    def description(self):
        return self.info['description']
        
    @description.setter
    def description(self, value):
        old_value = self.info['description']
        self.info['description'] = value
        if old_value != value: self.write() 


    @property
    def due(self):
        return self.info['due']
        
    @due.setter
    def due(self, value):
        old_value = self.info['due']
        self.info['due'] = value
        if old_value != value: self.write()    


    @property
    def project(self):
        return self.info['project']

    @project.setter
    def project(self, value):
        self.info['project'] = value
        self.projects += [value]
        self.write()


    @property
    def importance(self):
        return self.info['importance']

    @importance.setter
    def importance(self, value: int):
        old_value = self.info['importance']
        self.info['importance'] = value
        if old_value != value: self.write()

    
    @property
    def created(self):
        return self.info['created']
        
    @created.setter
    def created(self, value):
        old_value = self.info['created']
        self.info['created'] = value
        if old_value != value: self.write()


    def is_active(self):
        return self.status == Project.ACTIVE

    def is_completed(self):
        return self.status == Project.COMPLETED


Project = decorate_class(Project, debugger(logger, 'Project'))
