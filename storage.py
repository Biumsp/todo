from todo_utilities import print, filesIO, GitWrapper, num2str, never
from todo_utilities import fatal_error, get_valid_description
from todo_utilities import decorate_class, debugger, logger
from task import Task
from project import Project
import os, re

class LookupError(Exception): pass
class NameError(Exception): pass

class Storage():

    def __init__(self, path=os.path.expanduser('~/.todo_storage')):
        self.path = path
        self.projects_path = os.path.join(self.path, '.projects')
        self.__init()
        self.git = GitWrapper(path)

        Project.path = self.projects_path
        Task.storage = self

        self.tasks = self._get_tasks()
        self.projects = self._get_projects()
        

    def __init(self):
        if not os.path.isdir(self.path):
            filesIO.mkdir(self.path)

        if not os.path.isfile(self.projects_path):
            filesIO.write(self.projects_path, {}, dumps=True)


    def _get_tasks(self):
        tasks = []
        for task_file in os.listdir(self.path):
            if task_file.endswith('.task'):
                task_file = task_file.replace('.task', '')
                tasks.append(Task(task_file))

        return tasks    


    def _get_projects(self):
        dict_projects = filesIO.read(self.projects_path, loads=True)
        projects = []
        for p_name in dict_projects:
            p_dict = dict_projects[p_name]
            projects.append(Project(p_dict)) 

        return projects


    def update(self):
        # Compute the values of tasks and projects
        pass


    def _project_lookup(self, name):
        '''Matches the name with the existing projects and completes it'''

        matches = [p for p in self.projects if name in p.name]
                
        if len(matches) > 1:
            fatal_error(f'ambiguous name "{name}" for project')

        if len(matches) == 0:
            fatal_error(f'no project named "{name}"')
        
        return matches[0].name

    
    def _task_lookup(self, name):
        '''Matches the name with the existing tasks and completes it'''

        matches = [t for t in self.tasks if t.iname == int(name)]

        if len(matches) == 0:
            fatal_error(f'no task numbered "{name}"')
        
        return matches[0].name


    def validate_project_name(self, name):
        '''Validates the name of a project'''

        if name in [p.name for p in self.projects]:
            fatal_error(f'project "{name}" already exists')
        
        if not re.match(r'^[a-zA-Z0-9_]+$', name):
            fatal_error(f'project "{name}" contains invalid characters')

        if len(name) > 25:
            fatal_error(f'project "{name}" is too long')

        if len(name) < 3:
            fatal_error(f'project "{name}" is too short')

        if name.lower() != name:
            fatal_error(f'project "{name}" must be lowercase')


    def _available_task_name(self):
        if self.tasks:
            return num2str(max([t.iname for t in self.tasks]) + 1)
        else:
            return '0000'


    def add(self, projects, new_projects, description, after, before, commit):

        for i, p in enumerate(projects):
            projects[i] = self._project_lookup(p)
        
        for i, p in enumerate(new_projects):
            self.validate_project_name(p)

        for i, t in enumerate(after):
            after[i] = self._task_lookup(t)

        for i, t in enumerate(before):
            before[i] = self._task_lookup(t)
            
        all_projects = projects + new_projects            
        description = get_valid_description(description)

        name = self._available_task_name()
        task = Task(name)

        task.description = description
        self.add_projects_to_task(all_projects, task=task)
        self.add_due_to_task(self._get_due(all_projects), task=task)
        self.add_following_to_task(after, task=task)
        self.add_followers_to_task(before, task=task)

        for t in after:
            self.add_followers_to_task([task.name], task_name=t)

        for t in before:
            self.add_following_to_task([task.name], task_name=t)
        
        if not commit: commit = f'Add task "{name}"'

        self.git.commit(task.path, commit)
        self.git.commit(self.projects_path, 'Update projects')

    
    def add_followers_to_task(self, followers, task_name=None, task=None, replace=False):
        if task is None:task = self._get_task_by_name(task_name)
        followers = set(followers)        

        if replace: task.followers = list(followers)
        else: 
            for p in task.followers: followers.add(p)
            task.followers = list(followers)


    def add_following_to_task(self, following, task_name=None, task=None, replace=False):
        if task is None:task = self._get_task_by_name(task_name)
        following = set(following)        

        if replace: task.following = list(following)
        else: 
            for p in task.following: following.add(p)
            task.following = list(following)
            

    def add_projects_to_task(self, projects, task_name=None, task=None, replace=False):
        if task is None:task = self._get_task_by_name(task_name)
        projects = set(projects)        

        if replace: task.projects = list(projects)
        else: 
            for p in task.projects: projects.add(p)
            task.projects = list(projects)


    def add_due_to_task(self, date, task_name=None, task=None, force=False):
        if task is None:task = self._get_task_by_name(task_name)

        for p in task.projects:
            if p.due < date:
                if force: 
                    print(f'Moving project "{p.name}" due date from {p.due} to {date}')
                    p.due = date
                else:
                    fatal_error(f'cannot set due date to {date}, project "{p.name}" expires on {p.due}')
        
        task.due = date


    def _get_task_by_name(self, name):
        name = self._task_lookup(name)
        return [t for t in self.tasks if t.name == name][0]

       
    def _get_due(self, projects):
        projects.sort(key=lambda p: p.due)

        return projects[0].due if projects else never()

    def __str__(self):
        return f'<Storage>'


    def __repr__(self):
        return f'<Storage>'

Storage = decorate_class(Storage, debugger(logger, 'Storage'))