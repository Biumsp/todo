from .utilities import filesIO, never
from .utilities import decorate_class, debugger, logger
import math


class Project():
    path = ''
    ACTIVE = 'active'
    COMPLETED = 'completed'

    def __init__(self, name):
        self._name = name
        self.value = 0
        self.status = Project.ACTIVE
        self.info = self.read() # All static attributes of the project 
        self.urgency = 0
        self.write()


    @property
    def name(self):
        return self._name
        
    @name.setter
    def name(self, value):
        old_value = self.name
        self._name = value
        self.info['name'] = value
        if old_value != value: self.write() 


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
    def priority(self):
        return self.info['priority']


    @property
    def importance(self):
        return self.info['importance']

    @importance.setter
    def importance(self, value: int):
        old_value = self.info['importance']
        self.info['importance'] = value
        if old_value != value: self.write()


    def _newborn_info(self):
        return {
            'name': self._name,
            'importance': 0,
            'due': never(),
            'description': ''
        }


    def __str__(self):
        return f'<Project {self._name}>'


    def __repr__(self):
        return f'<Project {self._name}>'


    def read(self):
        projects = filesIO.read(Project.path, loads=True)
        try: 
            info = projects[self._name]
        except KeyError:
            info = self._newborn_info()

        return info


    def write(self):
        projects = filesIO.read(Project.path, loads=True)
        try: 
            projects[self._name] = self.info
        except KeyError:
            projects.update({self._name: self.info})

        filesIO.write(Project.path, projects, dumps=True)


Project = decorate_class(Project, debugger(logger, 'Project'))
