from todo_utilities import print, filesIO, GitWrapper, num2str, never
from todo_utilities import fatal_error, get_valid_description
from todo_utilities import decorate_class, debugger, logger, _c
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
            projects.append(Project(p_name))
            for t in self.active_tasks():
                if p_name in t.projects:
                    projects[-1].restore()

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

    def edit(self, name, projects, new_projects, after, before, due, override, commit):
        task = self._get_task_by_name(name)

        if not any([projects, new_projects, after, before, due, override]):
            task.description = get_valid_description(None, task.description)

        for i, p in enumerate(projects):
            projects[i] = self._project_lookup(p)
        
        for i, p in enumerate(new_projects):
            self.validate_project_name(p)

        for i, t in enumerate(after):
            after[i] = self._task_lookup(t)

        for i, t in enumerate(before):
            before[i] = self._task_lookup(t)

        all_projects = projects + new_projects
        if all_projects: 
            self.add_projects_to_task(all_projects, task=task, override=override)

        if after:
            self.add_following_to_task(after, task=task, override=override)
            for t in after:
                self.add_followers_to_task([task.name], task_name=t)       

        if before:
            self.add_followers_to_task(before, task=task, override=override)
            for t in before:
                self.add_following_to_task([task.name], task_name=t) 

        if due:
            self.add_due_to_task(due, task=task)

        if not commit: commit = f'Edit task "{name}"'
        self.git.commit(task.path, commit)


    def add(self, projects, new_projects, description, after, before, due, commit):

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

    
    def add_followers_to_task(self, followers, task_name=None, task=None, override=False):
        if task is None:task = self._get_task_by_name(task_name)
        followers = set(followers)        

        if override: task.followers = list(followers)
        else: 
            for p in task.followers: followers.add(p)
            task.followers = list(followers)


    def add_following_to_task(self, following, task_name=None, task=None, override=False):
        if task is None:task = self._get_task_by_name(task_name)
        following = set(following)        

        if override: task.following = list(following)
        else: 
            for p in task.following: following.add(p)
            task.following = list(following)
            

    def add_projects_to_task(self, projects_names, task_name=None, task=None, override=False):
        if task is None:task = self._get_task_by_name(task_name)
        projects_names = set(projects_names)        

        if override: task.projects = list(projects_names)
        else: 
            for p in task.projects: projects_names.add(p)
            task.projects = list(projects_names)


    def add_due_to_task(self, date, task_name=None, task=None, override=False):
        if task is None:task = self._get_task_by_name(task_name)

        for p in [Project(p) for p in task.projects]:
            if p.due < date:
                if override: 
                    print(f'Moving project "{p.name}" due date from {p.due} to {date}')
                    p.due = date
                else:
                    fatal_error(f'cannot set due date to {date}, project "{p.name}" expires on {p.due}')
        
        task.due = date


    def _get_task_by_name(self, name):
        name = self._task_lookup(name)
        return [t for t in self.tasks if t.name == name][0]

       
    def _get_due(self, projects_names):
        projects = [Project(p) for p in projects_names]
        projects.sort(key=lambda p: p.due)

        return projects[0].due if projects else never()

    def __str__(self):
        return f'<Storage>'


    def __repr__(self):
        return f'<Storage>'


    def done(self, task_name, commit=None):
        task = self._get_task_by_name(task_name)

        task.done()

        if not commit: commit = f'Mark task "{task_name}" as done'
        self.git.commit(task.path, commit)

    
    def restore(self, task_name, commit=None):
        task = self._get_task_by_name(task_name)

        task.restore()

        if not commit: commit = f'Restore task "{task_name}"'
        self.git.commit(task.path, commit)

    
    def delete(self, task_name, commit=None):
        task = self._get_task_by_name(task_name)

        task.delete()

        if not commit: commit = f'Delete task "{task_name}"'
        self.git.commit(task.path, commit)


    def compute_importance(self):
        def compute_task_importance(task, visited):
            followers = [Task(t) for t in task.followers]
            followers = [t for t in followers if t.active()]

            tot = 1
            visited.append(task.name)
            for t in followers:
                if not t.name in visited:
                    tot += compute_task_importance(t, visited)
            
            return tot

        for task in self.tasks:
            task.importance = compute_task_importance(task, [])


    def active_tasks(self):
        return [t for t in self.tasks if t.active()]


    def list(self, sort, projects, active, completed, deleted, limit, info, one_line):
        self.compute_importance()

        if sort in ['importance', 'I'] or info: 
            self.tasks.sort(key=lambda t: t.importance, reverse=True)
        else:
            self.tasks.sort(key=lambda t: t.urgency)

        tasks = []
        for t in self.tasks:
            if t.deleted() and not deleted: continue
            if t.completed() and not completed: continue
            if t.active() and not active: continue
            for p in projects:
                if p not in t.projects: continue

            tasks.append(t)

        if limit < len(tasks): tasks = tasks[:limit]

        output = []
        if info and one_line:
            if info > 2:
                output.append((_c.orange + '{:^5} {:^19} {:4} {:^6} - {}' + _c.reset).format(
                    'ID', 'due-date', 'status', 'I/U', 'description'))

                for t in tasks:
                    output.append((_c.green + '{:5} {:19} {:^6} {:>2}/{:<3} - ' + _c.reset).format(
                        t.name, t.due, t.status, t.importance, 100//max(t.urgency, 1)) + t.description.splitlines()[0])

            elif info == 2:
                output.append((_c.orange + '{:^5} {:4} {:^6} - {}' + _c.reset).format(
                    'ID', 'status', 'I/U', 'description'))

                for t in tasks:
                    output.append((_c.green + '{:5} {:^6} {:>2}/{:<3} - ' + _c.reset).format(
                        t.name, t.status, t.importance, 100//max(t.urgency, 1)) + t.description.splitlines()[0])

            elif info == 1:
                output.append((_c.orange + '{:^5} {:^6} - {}' + _c.reset).format(
                    'ID', 'I/U', 'description'))

                for t in tasks:
                    output.append((_c.green + '{:5} {:>2}/{:<3} - ' + _c.reset).format(
                        t.name, t.importance, 100//max(t.urgency, 1)) + t.description.splitlines()[0])
                    

        elif info and not one_line:
            if info > 2:
                for t in tasks:
                    out = (_c.orange + 'ID: {:5}\nstatus: {:^6}\ndue-date: {:19}\nI/U: {:>3}/{:<3}' + _c.reset).format(
                        t.name, t.status, t.due, t.importance, 100//max(t.urgency, 1))
                    out += '\n\t' + t.description.replace('\n', '\n\t')
                    output.append(out)

            elif info == 2:
                for t in tasks:
                    out = (_c.orange + 'ID: {:5}\nstatus: {:^6}\nI/U: {:>3}/{:<3}' + _c.reset).format(
                        t.name, t.status, t.due, t.importance, 100//max(t.urgency, 1))
                    out += '\n\t' + t.description.replace('\n', '\n\t')
                    output.append(out)

            elif info == 1:
                for t in tasks:
                    out = (_c.orange + 'ID: {:5}\nI/U: {:>3}/{:<3}' + _c.reset).format(
                        t.name, t.status, t.due, t.importance, 100//max(t.urgency, 1))
                    out += '\n\t' + t.description.replace('\n', '\n\t')
                    output.append(out)


        elif not info and one_line:
            output.append(_c.orange + '  ID  - description' + _c.reset)
            for t in tasks:
                out = (_c.green + '{:5} - ' + _c.reset).format(
                    t.name) + t.description.splitlines()[0] 
                output.append(out)


        elif not info and not one_line:
            for t in tasks:
                out = ((_c.green + 'ID: {}\n\t' + _c.reset).format(t.name))
                out += '\n\t' + t.description.replace('\n', '\n\t')
                output.append(out)


        print('\n'.join(output))


    def list_projects(self, sort, limit, active, completed):
        self.compute_importance()

        if sort in ['importance', 'I']: 
            self.projects.sort(key=lambda p: p.importance, reverse=True)
        else:
            self.projects.sort(key=lambda p: p.urgency)

        projects = []
        for p in self.projects:
            if p.completed() and not completed: continue
            if p.active() and not active: continue

            projects.append(p)

        if limit < len(projects): projects = projects[:limit]

        output = []
        for p in projects:
            output.append((_c.green + '{:4} - {:19} - {:>2}/{:<3} ' + _c.reset + '{}').format(
                p.status, p.due, p.importance, 100//max(p.urgency, 1), p.name))

        print('\n'.join(output))

#Storage = decorate_class(Storage, debugger(logger, 'Storage'))