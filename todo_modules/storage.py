from datetime import time
from .utilities import print, filesIO, GitWrapper, num2str, now
from .utilities import fatal_error, get_valid_description
from .utilities import decorate_class, debugger, logger, _c
from .task import Task
from .project import Project
import os, re

class LookupError(Exception): pass
class NameError(Exception): pass

class Storage():

    def __init__(self, path):
        self.path = path
        self.projects_path = os.path.join(self.path, '.projects')
        self.__init()
        self.git = GitWrapper(path)

        Project.path = self.projects_path
        Task.storage = self

        self.tasks = self._get_tasks()
        self.projects = self._get_projects()
        self.refresh()
        

    def __init(self):
        if not os.path.isdir(self.path):
            filesIO.mkdir(self.path)

        if not os.path.isfile(self.projects_path):
            filesIO.write(self.projects_path, {}, dumps=True)

    
    def _validate_date(self, date):
        today = now(date=True)
        if date.year == 1900: 
            date = date.replace(year=today.year)
            if date < now(date=True): 
                date = date.replace(year=today.year+1)

        if date < now(date=True): fatal_error('date cannot be in the past')
        return date.strftime(r"%Y-%m-%d")


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

        return projects


    def _project_lookup(self, name):
        '''Matches the name with the existing projects and completes it'''

        matches = [p for p in self.projects if name in p.name]
                
        if len(matches) > 1:
            fatal_error(f'ambiguous name "{name}" for project')

        if len(matches) == 0:
            fatal_error(f'no project named "{name}"')
        
        return matches[0].name

    
    def _get_project_by_name(self, project_name):
        project_name = self._project_lookup(project_name)
        return [p for p in self.projects if p.name == project_name][0]

    
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


    def new_project(self, name, due, priority, importance, commit):
        self.validate_project_name(name)

        project = Project(name)
        project.due = self._validate_date(due)
        project.priority = priority
        project.importance = int(importance)

        if not commit: commit = f'Create project "{name}"'
        self.git.commit(project.path, commit)

        print(f'Created project {name}')


    def edit(self, name, projects, new_projects, after, before, due, override, commit):
        task = self._get_task_by_name(name)
        if due is not None: due = self._validate_date(due)

        if not any([projects, new_projects, after, before, due]):
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

        print(f'Edited task {task.name}: {task.description.splitlines()[0]}')


    def _replace_project_in_tasks(self, old_name, new_name):
        for t in self.tasks:
            if old_name in t.projects:
                t.projects = [p if p != old_name else new_name for p in t.projects]

    
    def edit_project(self, project_name, name, due, priority, importance, commit):
        project = self._get_project_by_name(project_name)
        if due is not None: due = self._validate_date(due)

        if due: project.due = due
        if name: 
            old_name = project.name
            project.name = name
            self._replace_project_in_tasks(old_name, name)

        if not commit: commit = f'Edit project "{project.name}"'
        self.git.commit(self.projects_path, commit)

        print(f'Edited project {old_name if name else project.name}')


    def add(self, project, description, after, before, time, commit):
        if due is not None: due = self._validate_date(due)

        project = self._project_lookup(project)

        for i, t in enumerate(after):
            after[i] = self._task_lookup(t)

        for i, t in enumerate(before):
            before[i] = self._task_lookup(t)

        description = get_valid_description(description)

        name = self._available_task_name()
        task = Task(name)

        task.description = description
        task.time = time

        task.main_project = project.name

        self.add_following_to_task(after, task=task)
        self.add_followers_to_task(before, task=task)
        
        if not commit: commit = f'Create task "{name}"'

        self.refresh()
        self.git.commit(task.path, commit)
        print(f'Created task {task.name}')

    
    def add_followers_to_task(self, followers, task_name=None, task=None, override=False):
        assert task or task_name
        
        if task is None:task = self._get_task_by_name(task_name)
        followers = set(followers)        

        if override: task.followers = list(followers)
        else: 
            for p in task.followers: followers.add(p)
            task.followers = list(followers)


    def add_following_to_task(self, following, task_name=None, task=None, override=False):
        assert task or task_name
        
        if task is None:task = self._get_task_by_name(task_name)
        following = set(following)        

        if override: task.following = list(following)
        else: 
            for p in task.following: following.add(p)
            task.following = list(following)
            

    def add_projects_to_task(self, projects_names, task_name=None, task=None, override=False):
        assert task or task_name
        
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

       
    def _get_closest_due(self, projects_names):
        projects  = [Project(p) for p in projects_names]
        due_dates = [p.due for p in projects]
        due_dates.sort()

        return due_dates[0]


    def _get_average_priority(self, projects_names):
        projects = [Project(p) for p in projects_names]
        p = [p.priority for p in projects]
        wp = [x.priority**2 for x in p]

        return sum(wp)/sum(p)


    def __str__(self):
        return f'<Storage>'


    def __repr__(self):
        return f'<Storage>'


    def done(self, task_name, commit=None):
        task = self._get_task_by_name(task_name)

        task.done()

        if not commit: commit = f'Mark task "{task_name}" as done'
        self.git.commit(task.path, commit)

        print(f'Completed task {task.name}: {task.description.splitlines()[0]}')

    
    def restore(self, task_name, commit=None):
        task = self._get_task_by_name(task_name)

        task.restore()

        if not commit: commit = f'Restore task "{task_name}"'
        self.git.commit(task.path, commit)

        print(f'Restored task {task.name}: {task.description.splitlines()[0]}')

    
    def delete(self, task_name, commit=None):
        task = self._get_task_by_name(task_name)

        task.delete()

        if not commit: commit = f'Delete task "{task_name}"'
        self.git.commit(task.path, commit)

        print(f'Deleted task {task.name}: {task.description.splitlines()[0]}')


    def compute_importance(self):
        def compute_task_importance(task, tasks, visited):
            followers = [Task(t) for t in task.followers]
            followers = set(followers).intersection(tasks)
            
            tot = 1
            visited.append(task.name)
            for t in followers:
                if not t.name in visited:
                    tot += compute_task_importance(t, tasks, visited)
            
            return tot

        for project in self.projects:
            tasks = [t for t in self.tasks if project.name in t.projects and t.is_active()]
            imp = []

            for task in tasks:
                imp.append(compute_task_importance(task, set(tasks), []))
            
            imp = [i/sum(imp)*project.importance for i in imp]
            for t, i in zip(tasks, imp): t.importance += i


    def refresh(self):

        for _ in range(4):
            for t in self.tasks:
                if not t.is_active(): continue

                following_tasks = [self._get_task_by_name(name) for name in t.following]
                for ft in following_tasks:
                    if not ft.is_active(): continue
                    if t.name not in ft.followers: ft.followers = ft.followers.append(t.name)

                sp = set(t.projects)
                followers_tasks = [self._get_task_by_name(name) for name in t.followers]
                for ft in followers_tasks:
                    if not ft.is_active(): continue
                    if t.name not in ft.following: ft.following = ft.following.append(t.name)
                    sp = sp.union(set(ft.projects))
                
                sp.remove(t.main_project)
                t.secondary_projects = list(sp)


        for t in self.tasks:
            if not t.is_active(): continue
            t.due = self._get_closest_due(t.projects)
            t.priority = self._get_average_priority(t.projects)
            t.urgency = t._get_urgency()
        
        self.compute_importance()


    def active_tasks(self):
        return [t for t in self.tasks if t.is_active()]


    def show(self, task_name):
        t = self._get_task_by_name(task_name)

        print('ID: {}\nI/U {}/{}\nstatus: {}\ncreated: {}\ncompleted: {}\ndeleted: {}\ndue date: {}\ntime: {}\npriority: {}\n   {}'.format(
            t.name,
            t.importance, 
            t.urgency, 
            t.status, 
            t.created, t.completed, 
            t.deleted, 
            t.due, 
            t.time,
            t.priority,
            t.description.replace('\n', '\n   ')
        ))


    def list(self, sort, projects, active, completed, deleted, limit, info, one_line):

        if sort in ['importance', 'I']: 
            self.tasks.sort(key=lambda t: t.urgency, reverse=True)
            self.tasks.sort(key=lambda t: t.importance, reverse=True)
        else:
            self.tasks.sort(key=lambda t: t.importance, reverse=True)
            self.tasks.sort(key=lambda t: t.urgency, reverse=True)

        projects = [self._project_lookup(p) for p in projects]
        tasks = []
        for t in self.tasks:
            stop = False
            if t.is_deleted() and not deleted: continue
            if t.is_completed() and not completed: continue
            if t.is_active() and not active: continue
            for p in projects: 
                if p not in t.projects: stop = True
            if stop: continue

            tasks.append(t)

        if limit < len(tasks): tasks = tasks[:limit]

        if info and one_line:
            if info > 2:
                print.add((_c.orange + '{:^5} {:^10} {:4} {:^6} - {}' + _c.reset).format(
                    'ID', 'due-date', 'status', 'I/U', 'description'))

                for t in tasks:
                    print.add((_c.green + '{:5} {:10} {:^6} {:>2}/{:<3} - ' + _c.reset).format(
                        t.name, t.due, t.status, t.importance, t.urgency) + t.description.splitlines()[0])

            elif info == 2:
                print.add((_c.orange + '{:^5} {:4} {:^6} - {}' + _c.reset).format(
                    'ID', 'status', 'I/U', 'description'))

                for t in tasks:
                    print.add((_c.green + '{:5} {:^6} {:>2}/{:<3} - ' + _c.reset).format(
                        t.name, t.status, t.importance, t.urgency) + t.description.splitlines()[0])

            elif info == 1:
                print.add((_c.orange + '{:^5} {:^6} - {}' + _c.reset).format(
                    'ID', 'I/U', 'description'))

                for t in tasks:
                    print.add((_c.green + '{:5} {:>2}/{:<3} - ' + _c.reset).format(
                        t.name, t.importance, t.urgency) + t.description.splitlines()[0])
                    

        elif info and not one_line:
            if info > 2:
                for t in tasks:
                    out = (_c.orange + 'ID: {:5}\nstatus: {:^6}\ndue-date: {:10}\nI/U: {:>3}/{:<3}' + _c.reset).format(
                        t.name, t.status, t.due, t.importance, t.urgency)
                    out += '\n   ' + t.description.replace('\n', '\n   ')
                    print.add(out)

            elif info == 2:
                for t in tasks:
                    out = (_c.orange + 'ID: {:5}\nstatus: {:^6}\nI/U: {:>3}/{:<3}' + _c.reset).format(
                        t.name, t.status, t.due, t.importance, t.urgency)
                    out += '\n   ' + t.description.replace('\n', '\n   ')
                    print.add(out)

            elif info == 1:
                for t in tasks:
                    out = (_c.orange + 'ID: {:5}\nI/U: {:>3}/{:<3}' + _c.reset).format(
                        t.name, t.status, t.due, t.importance, t.urgency)
                    out += '\n   ' + t.description.replace('\n', '\n   ')
                    print.add(out)


        elif not info and one_line:
            print.add(_c.orange + '  ID  - description' + _c.reset)
            for t in tasks:
                out = (_c.green + '{:5} - ' + _c.reset).format(
                    t.name) + t.description.splitlines()[0] 
                print.add(out)


        elif not info and not one_line:
            for t in tasks:
                out = ((_c.green + 'ID: {}' + _c.reset).format(t.name))
                out += '\n   ' + t.description.replace('\n', '\n   ')
                print.add(out)


        print.empty()


    def list_projects(self, sort, limit, active, completed):

        if sort in ['importance', 'I']: 
            self.projects.sort(key=lambda p: p.urgency, reverse=True)
            self.projects.sort(key=lambda p: p.importance, reverse=True)
        else:
            self.projects.sort(key=lambda p: p.importance, reverse=True)
            self.projects.sort(key=lambda p: p.urgency, reverse=True)

        projects = []
        for p in self.projects:
            if p.is_completed() and not completed: continue
            if p.is_active() and not active: continue

            projects.append(p)

        if limit < len(projects): projects = projects[:limit]

        print.add((_c.orange + '{:6} {:10} {:^6} {}' + _c.reset).format(
                'status', 'due-date', 'I/U', 'name'))
        for p in projects:
            print.add((_c.green + '{:6} {:10} {:>2}/{:<3} ' + _c.reset + '{}').format(
                p.status, p.due, p.importance, p.urgency, p.name))

        print.empty()

#Storage = decorate_class(Storage, debugger(logger, 'Storage'))