import os, math
from .utilities import filesIO, now, never, diff_dates
from .utilities import decorate_class, debugger, logger

class Task():
    TODO = 'todo'
    DONE = 'done'
    DEL = 'del'

    storage = None
    
    def __init__(self, name):
        self.name = name
        self.iname = int(name)
        self.path = os.path.join(Task.storage.path, name + '.task')
        self.info = self.read() # All static attributes of the task
        
        self.urgency    = 0
        self.importance = 0
        self.priority   = 0


    def _get_urgency(self):
        if not self.is_active(): return 0
        
        time_left = diff_dates(self.info['due'], now())
        hours_per_day = (self.priority*2 + 0.5)
        days_to_complete = self.time/hours_per_day

        urgency = time_left - days_to_complete
        urgency = 100//max(urgency, 1)

        return math.floor(urgency)


    def _newborn_info(self):
        return {
            'description': '',
            'status': Task.TODO,
            'following': [],
            'followers': [],
            'main_project': None,
            'secondary_projects': [],
            'projects': [],
            'time': 1,
            'priority': 0,
            'created': now(),
            'completed': None,
            'deleted': None
        }


    def __str__(self):
        return f'<Task {self.name}>'


    def __repr__(self):
        return f'<Task {self.name}>'


    def read(self):
        if os.path.isfile(self.path):
            info = filesIO.read(self.path, loads=True)
        else:
            info = self._newborn_info()
        return info


    def write(self):
        filesIO.write(self.path, self.info, dumps=True)


    @property
    def status(self):
        return self.info['status']
        

    @property
    def following(self):
        return self.info['following']
        
    @following.setter
    def following(self, value):
        old_value = self.info['following']
        self.info['following'] = value
        if old_value != value: self.write()


    @property
    def followers(self):
        return self.info['followers']
        
    @followers.setter
    def followers(self, value):
        old_value = self.info['followers']
        self.info['followers'] = value
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
    def main_project(self):
        return self.info['description']
        
    @main_project.setter
    def main_project(self, value):
        old_value = self.info['main_project']
        self.info['main_project'] = value
        self.info['projects'] = self.info['secondary_projects'] + [value]
        if old_value != value: self.write()


    @property
    def projects(self):
        return self.info['projects']


    @property
    def secondary_projects(self):
        return self.info['secondary_projects']
        
    @secondary_projects.setter
    def secondary_projects(self, value):
        old_value = self.info['secondary_projects']
        self.info['secondary_projects'] = value
        self.info['projects'] = [self.info['main_project']] + value
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
    def created(self):
        return self.info['created']
        
    @created.setter
    def created(self, value):
        old_value = self.info['created']
        self.info['created'] = value
        if old_value != value: self.write()

    
    @property
    def completed(self):
        return self.info['completed']
        
    @completed.setter
    def is_completed(self, value):
        old_value = self.info['completed']
        self.info['completed'] = value
        if old_value != value: self.write()


    @property
    def time(self):
        return self.info['time']
        
    @time.setter
    def time(self, value):
        old_value = self.info['time']
        self.info['time'] = value
        if old_value != value: self.write()

    
    @property
    def deleted(self):
        return self.info['deleted']
        
    @deleted.setter
    def is_deleted(self, value):
        old_value = self.info['deleted']
        self.info['deleted'] = value
        if old_value != value: self.write()
            

    def done(self):
        self.info['status'] = Task.DONE
        self.info['completed'] = now()
        self.write()


    def restore(self):
        self.info['status'] = Task.TODO
        self.info['completed'] = None
        self.info['deleted'] = None
        self.write()   


    def delete(self):
        self.info['status'] = Task.DEL
        self.info['deleted'] = now()
        self.write()


    def is_active(self):
        return self.info['status'] == Task.TODO


    def is_completed(self):
        return self.info['status'] == Task.DONE
        

    def is_deleted(self):
        return self.info['deleted'] is not None

#Task = decorate_class(Task, debugger(logger, 'Task'))
