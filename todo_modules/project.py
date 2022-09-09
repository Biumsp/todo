from .utilities import filesIO, never, diff_dates, now
from .utilities import decorate_class, debugger, logger
import math


class Project():
    path = ''

    def __init__(self, name):
        self._name = name
        self.value = 0
        self.info = self.read() # All static attributes of the project 
        self.write()

        self.urgency = 0
        self.importance = 0


    def compute_urgency(self):
        time_left = diff_dates(self.info['due'], now())
        hours_per_day = (self.priority*2 + 0.5)
        days_to_complete = self.time/hours_per_day
        
        urgency = time_left-days_to_complete
        urgency = 100//max(urgency, 1)

        self.urgency = math.floor(urgency)


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

    @priority.setter
    def priority(self, value: int):
        old_value = self.info['priority']
        if value >= 3:
            self.info['priority'] = 3
        else:
            self.info['priority'] = value
        if old_value != value: self.write()


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
            'priority': 0,
            'due': never(),
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


#Project = decorate_class(Project, debugger(logger, 'Project'))
