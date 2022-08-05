from todo_utilities import filesIO, never, diff_dates, now
from todo_utilities import decorate_class, debugger, logger

template = {
    'name': 'template_project',
    'due': None,
    'value': 0
}

class Project():
    path = ''

    DONE = 'done'
    TODO = 'todo'
    DEL = 'del'

    def __init__(self, name):
        self._name = name
        self.value = 0
        self.info = self.read()
        self.write()

        self.status = Project.DONE
        self.urgency = diff_dates(self.info['due'], now())
        self.importance = 0


    @property
    def name(self):
        return self._name
        
    @name.setter
    def name(self, value):
        self._name = value
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
            'name': self._name,
            'due': never()
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

    
    def restore(self):
        self.status = Project.TODO


    def active(self):
        return self.status == Project.TODO

    def completed(self):
        return self.status == Project.DONE

#Project = decorate_class(Project, debugger(logger, 'Project'))
