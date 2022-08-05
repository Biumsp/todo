import os
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
        self.info = self.read()

        self.urgency = diff_dates(self.info['due'], now())
        self.importance = 0


    def _newborn_info(self):
        return {
            'description': '',
            'status': Task.TODO,
            'following': [],
            'followers': [],
            'projects': [],
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
        self.info['description'] = value
        self.write()


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
    def projects(self):
        return self.info['projects']
        
    @projects.setter
    def projects(self, value):
        self.info['projects'] = value
        self.write()


    @property
    def due(self):
        return self.info['due']
        
    @due.setter
    def due(self, value):
        self.info['due'] = value
        self.write()

    
    @property
    def created(self):
        return self.info['created']
        
    @created.setter
    def created(self, value):
        self.info['created'] = value
        self.write()

    
    @property
    def completed(self):
        return self.info['completed']
        
    @completed.setter
    def completed(self, value):
        self.info['completed'] = value
        self.write()

    
    @property
    def deleted(self):
        return self.info['deleted']
        
    @deleted.setter
    def deleted(self, value):
        self.info['deleted'] = value
        self.write()
            

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

    def active(self):
        return self.info['status'] == Task.TODO

    def completed(self):
        return self.info['status'] == Task.DONE

    def deleted(self):
        return self.info['deleted'] is not None

Task = decorate_class(Task, debugger(logger, 'Task'))
