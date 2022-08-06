import os, math
from todo_utilities import filesIO, now, never, diff_dates
from todo_utilities import decorate_class, debugger, logger

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
        
        self.urgency = self._get_urgency()
        self.importance = 0


    def _get_urgency(self):
        time_left = diff_dates(self.info['due'], now())
        hours_per_day = (self.priority*2 + 0.5)
        days_to_complete = self.time/hours_per_day

        urgency = time_left//days_to_complete
        urgency = 100//max(urgency, 1)

        return math.floor(urgency)


    def _newborn_info(self):
        return {
            'description': '',
            'status': Task.TODO,
            'following': [],
            'followers': [],
            'projects': [],
            'time': 1,
            'priority': 0,
            'due': never(),
            'created': now(),
            'completed': None,
            'deleted': None,
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
    def description(self):
        return self.info['description']
        
    @description.setter
    def description(self, value):
        old_value = self.info['description']
        self.info['description'] = value
        if old_value != value: self.write()


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
    def projects(self):
        return self.info['projects']
        
    @projects.setter
    def projects(self, value):
        old_value = self.info['projects']
        self.info['projects'] = value
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
    def completed(self, value):
        old_value = self.info['completed']
        self.info['completed'] = value
        if old_value != value: self.write()


    @property
    def priority(self):
        return self.info['priority']
        
    @priority.setter
    def priority(self, value: int):
        if value >= 3:
            self.info['priority'] = 3
        else:
            old_value = self.info['priority']
            self.info['priority'] = value
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
    def deleted(self, value):
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
        if old_value != value: self.write()

    def active(self):
        return self.info['status'] == Task.TODO

    def completed(self):
        return self.info['status'] == Task.DONE

    def deleted(self):
        return self.info['deleted'] is not None

#Task = decorate_class(Task, debugger(logger, 'Task'))
