from asyncio import FastChildWatcher
import os
from .utilities import filesIO, now, never, diff_dates
from .utilities import decorate_class, debugger, logger

class Task():
    TODO = 'todo'
    DONE = 'done'
    INPROGRESS = 'in-progress'
    DEL = 'del'

    todolist = None
    
    def __init__(self, name):
        self.name = name
        self.iname = int(name)
        self.path = os.path.join(Task.todolist.path, name + '.task')
        self.info = self.read()
        
        self.urgency    = 0
        self.importance = 0
        self.projects   = [self.project] if self.project else [] 
        self.due = never()


    def _newborn_info(self):
        return {
            'description': '',
            'status': Task.TODO,
            'following': [],
            'followers': [],
            'project': '',
            'time': 1,
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
    def project(self):
        return self.info['project']

    @project.setter
    def project(self, value):
        self.info['project'] = value
        self.projects += [value]
        self.write()

    
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


    def doing(self):
        self.info['status'] = Task.INPROGRESS
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
        return self.info['status'] == Task.TODO or self.info['status'] == Task.INPROGRESS


    def is_completed(self):
        return self.info['status'] == Task.DONE

    
    def is_inprogress(self):
        return self.info['status'] == Task.INPROGRESS
        

    def is_deleted(self):
        return self.info['deleted'] is not None


    def is_scheduled(self):
        return self.info['created'] > now()
        

Task = decorate_class(Task, debugger(logger, 'Task'))
