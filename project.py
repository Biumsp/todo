from todo_utilities import filesIO, never
from todo_utilities import decorate_class, debugger, logger

template = {
    'name': 'template_project',
    'due': None,
    'value': 0
}

class Project(dict):
    path = ''

    def __init__(self, name):
        self.name = name
        self.value = 0
        self.info = self.read()
        self.write()


    @property
    def name(self):
        return self.name
        
    @name.setter
    def name(self, value):
        self.name = value
        self.info['name'] = value
        self.write()       


    @property
    def due(self):
        return self.info['due']
        
    @due.setter
    def due(self, value):
        self.info['due'] = value
        self.write()


    def _newborn_info(self):
        return {
            'name': self.name,
            'due': never()
        }

    def __str__(self):
        return f'<Project {self.name}>'


    def __repr__(self):
        return f'<Project {self.name}>'


    def read(self):
        projects = filesIO.read(Project.path, loads=True)
        try: 
            info = projects[self.name]
        except KeyError:
            info = self._newborn_info()

        return info


    def write(self):
        projects = filesIO.read(Project.path, loads=True)
        try: 
            projects[self.name] = self.info
        except KeyError:
            projects.update({self.name: self.info})

        filesIO.write(Project.path, projects, dumps=True)

Project = decorate_class(Project, debugger(logger, 'Project'))
