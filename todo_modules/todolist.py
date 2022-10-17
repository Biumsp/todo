from tkinter.messagebox import NO
from .utilities import print, filesIO, GitWrapper, num2str, now, never, diff_dates
from .utilities import fatal_error, get_valid_description
from .utilities import decorate_class, debugger, logger, _c
from .task import Task
from .project import Project
import os, math

class LookupError(Exception): pass
class NameError(Exception): pass

class TodoList():

    def __init__(self, path):
        self.path = path
        self.__init()
        self.git = GitWrapper(path)

        Project.todolist = self
        Task.todolist = self

        self.tasks = self._get_tasks()
        self.projects = self._get_projects()
        self.refresh()
        

    def __init(self):
        if not os.path.isdir(self.path):
            filesIO.mkdir(self.path)

    
    def _validate_date(self, date, past_is_ok=False):
        today = now(date=True)
        if date.year == 1900: 
            date = date.replace(year=today.year)
            if date < now(date=True) and not past_is_ok: 
                date = date.replace(year=today.year+1)

        if date < now(date=True) and not past_is_ok: print('Warning: date is in the past', color='orange')
        return date.strftime(r"%Y-%m-%d")


    def _get_tasks(self):
        tasks = []
        for file in os.listdir(self.path):
            if file.endswith('.task'):
                task_file = file.replace('.task', '')
                tasks.append(Task(task_file))

        return tasks    


    def _get_projects(self):
        projects = []
        for file in os.listdir(self.path):
            if file.endswith('.project'):
                project_file = file.replace('.project', '')
                projects.append(Project(project_file))

        return projects

    
    def _get_project_by_name(self, project_name):
        project_name = self._project_lookup(project_name).name
        return [p for p in self.projects if p.name == project_name][0]

    
    def _task_lookup(self, name):
        '''Matches the name with the existing tasks and completes it'''

        try: name = int(name)
        except: fatal_error(f'no task numbered "{name}"')

        matches = [t for t in self.tasks if t.iname == name]

        if len(matches) == 0:
            fatal_error(f'no task numbered "{name}"')
        
        return matches[0].name

    
    def _project_lookup(self, name):
        '''Matches the name with the existing projects and completes it'''

        try: name = int(name)
        except: fatal_error(f'no project numbered "{name}"')

        matches = [p for p in self.projects if p.iname == name]

        if len(matches) == 0:
            fatal_error(f'no project numbered "{name}"')
        
        return matches[0]



    def _available_task_name(self):
        if self.tasks:
            return num2str(max([t.iname for t in self.tasks]) + 1)
        else:
            return '0000'

    
    def _available_project_name(self):
        if self.projects:
            return num2str(max([p.iname for p in self.projects]) + 1)
        else:
            return '0000'


    def add(self, project, description, after, before, time, wait, commit):

        project = self._project_lookup(project)

        for i, t in enumerate(after):
            after[i] = self._task_lookup(t)

        for i, t in enumerate(before):
            before[i] = self._task_lookup(t)

        description = get_valid_description(description)

        name = self._available_task_name()
        task = Task(name)

        if wait: task.created = self._validate_date(wait)

        task.description = description
        task.time = time
        task.project = project.name

        self.add_followers_to_task(before, task=task)

        if after:
            for t in after:
                self.add_followers_to_task([task.name], task_name=t)
        
        if not commit: commit = f'Create task "{name}"'

        self.refresh()
        self.git.commit(task.path, commit)
        print(f'Created task {task.name}')


    def add_project(self, due, description, importance, commit):

        description = get_valid_description(description)

        name = self._available_project_name()
        project = Project(name)

        project.due = self._validate_date(due)
        project.importance = int(importance)
        project.description = description

        if not commit: commit = f'Create project "{name}"'
        self.git.commit(project.path, commit)

        print(f'Created project {name}')


    def edit(self, name, project, time, wait, after, before, override, commit):
        task = self._get_task_by_name(name)

        if not any([project, after, before, time is not None, wait]):
            task.description = get_valid_description(None, task.description)

        if project: project = self._project_lookup(project)

        if wait: task.created = self._validate_date(wait)

        for i, t in enumerate(after):
            after[i] = self._task_lookup(t)

        for i, t in enumerate(before):
            before[i] = self._task_lookup(t)

        if project: task.project = project.name

        if time is not None: task.time = time

        if after:
            for t in after:
                self.add_followers_to_task([task.name], task_name=t)       

        if before:
            self.add_followers_to_task(before, task=task, override=override)

        if not commit: commit = f'Edit task "{name}"'
        self.git.commit(task.path, commit)

        print(f'Edited task {task.name}: {task.description.splitlines()[0]}')

    
    def edit_project(self, project_name, due, importance, commit):
        project = self._get_project_by_name(project_name)

        try: 
            if due is not None: due = self._validate_date(due)
        except AttributeError: pass

        if due: project.due = due
                
        if importance: project.importance = importance

        if not any([importance, due]):
            description = get_valid_description(None, initial_message=project.description)
            project.description = description

        if not commit: commit = f'Edit project "{project.name}"'
        self.git.commit(project.path, commit)

        print(f'Edited project {project.name}')

    
    def add_followers_to_task(self, followers, task_name=None, task=None, override=False):
        assert task or task_name
        
        if task is None:task = self._get_task_by_name(task_name)
        followers = set(followers)        

        if override: task.followers = list(followers)
        else: 
            for p in task.followers: followers.add(p)
            task.followers = list(followers)
            

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

       
    def _get_closest_due(self, projects):
        due_dates = [p.due for p in projects]
        due_dates.sort()

        try: return due_dates[0]
        except IndexError: return never()


    def __str__(self):
        return f'<TodoList>'


    def __repr__(self):
        return f'<TodoList>'


    def done(self, task_name, commit):
        task = self._get_task_by_name(task_name)

        task.done()

        if not commit: commit = f'Mark task "{task_name}" as done'
        self.git.commit(task.path, commit)

        print(f'Completed task {task.name}: {task.description.splitlines()[0]}')

    
    def doing(self, task_name, commit):
        task = self._get_task_by_name(task_name)

        task.doing()

        if not commit: commit = f'Mark task "{task_name}" as in-progress'
        self.git.commit(task.path, commit)

        print(f'Working on task {task.name}: {task.description.splitlines()[0]}')

    
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
            followers = [self._get_task_by_name(t) for t in task.followers]
            followers = [t for t in followers if project.name in t.projects and t.is_active()]
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

        for t in self.tasks: t.importance = math.floor(t.importance)

    
    def _compute_project_urgency(self, p):

        WORKING_HOURS_PER_DAY = 4
        
        tasks = [t for t in self.tasks if p.name in t.projects and t.is_active()]

        if not tasks: return 0

        # Estimated completion time
        time = max(sum(t.time for t in tasks), 0.001)
        
        time_left = diff_dates(p.due, now()) # days
        time_left = time_left*WORKING_HOURS_PER_DAY     # hours           

        # How many times could you complete the project in the time left
        confidence = time_left/time

        urgency = 100//max([confidence, 1])

        return math.floor(urgency)

    
    def report(self, date_range, machine, info):
        
        start = self._validate_date(date_range[0], past_is_ok=True)
        stop  = self._validate_date(date_range[1], past_is_ok=True)

        tasks = []
        for t in self.tasks:
            if t.completed and start <= t.completed <= stop and t.time > 0: tasks.append(t)

        if not machine:

            if start == stop: print.add(f"Completed tasks on {start}")
            else: print.add(f"Completed tasks between {start} and {stop}")

            print.add(f"Total: {len(tasks)} tasks, {round(sum(t.time for t in tasks), 1)} [h]")

            if info == 2:
                print.add('{:^4} {:^10} {:^4} - {}'.format('ID', 'due-date', 'P-ID', 'description'), color='orange')

                for t in tasks:
                    print.add('{:4} {:10} {:^4} - {}'.format(t.name, t.due, t.project, t.description.splitlines()[0]))

            if info == 1:
                print.add('{:^4} {:^4} {:^4} - {}'.format('ID', 'P-ID', 'time', 'description'), color='orange')

                for t in tasks:
                    print.add('{:^4} {:^4} {:^4} - {}'.format(t.name, t.project, t.time, t.description.splitlines()[0]))

            else:
                print.add('{:^4} {:^4} - {}'.format('ID', 'P-ID', 'description'), color='orange')

                for t in tasks:
                    print.add('{:4} {:^4} - {}'.format(t.name, t.project, t.description.splitlines()[0]))

            print.empty()


    def refresh(self):

        for _ in range(4):
            for t in self.tasks:
                if not t.is_active(): continue

                sp = set(t.projects)
                followers_tasks = [self._get_task_by_name(name) for name in t.followers]
                for ft in followers_tasks:
                    if not ft.is_active(): continue
                    if t.name not in ft.following: ft.following += [t.name]
                    sp = sp.union(set(ft.projects))

                following_tasks = [self._get_task_by_name(name) for name in t.following]
                for ft in following_tasks:
                    if not ft.is_active(): continue
                    if t.name not in ft.followers: ft.followers += [t.name]

                t.projects = list(sp)

        for p in self.projects:
            p.urgency = self._compute_project_urgency(p)

        for t in self.tasks:
            projects = [self._get_project_by_name(p) for p in t.projects]
            t.due = self._get_closest_due(projects)
            t.urgency = max([p.urgency for p in projects])
        
        self.compute_importance()


    def show(self, task_name):
        t = self._get_task_by_name(task_name)
        project = self._get_project_by_name(t.project)

        print('ID: {}\nI/U {}/{}\nstatus: {}\nproject: {}\ndue: {}\ntime: {} [h]\nfollowing: {}\nfollowers: {}\ncreated: {}\ncompleted: {}\ndeleted: {}\n   {}'.format(
            t.name,
            t.importance, t.urgency, 
            t.status, 
            project.name,
            project.due,
            t.time,
            ''.join(t.following),
            ''.join(t.followers),
            t.created, t.completed, t.deleted, 
            t.description.replace('\n', '\n   ')
        ))

    def show_project(self, project_name):
        p = self._get_project_by_name(project_name)

        print('ID: {}\nI/U {}/{}\nstatus: {}\ndue date: {}\n   {}'.format(
            p.name,
            p.importance, 
            p.urgency, 
            p.status, 
            p.due, 
            p.description.replace('\n', '\n   ')
        ))

    def list(self, sort, projects, active, completed, deleted, waiting, filter, filter_project, limit, info, one_line):

        if sort in ['importance', 'I']: 
            self.tasks.sort(key=lambda t: t.name, reverse=True)
            self.tasks.sort(key=lambda t: t.urgency, reverse=True)
            self.tasks.sort(key=lambda t: t.importance, reverse=True)

        elif sort in ['creation', 'C']:
            self.tasks.sort(key=lambda t: t.name, reverse=True)

        else:
            self.tasks.sort(key=lambda t: t.name, reverse=True)
            self.tasks.sort(key=lambda t: t.importance, reverse=True)
            self.tasks.sort(key=lambda t: t.urgency, reverse=True)

        projects = [self._project_lookup(p) for p in projects]
        tasks = []
        inprogress = []
        scheduled = []
        for t in self.tasks:
            stop = True
            if t.is_scheduled(): scheduled.append(t); continue
            if t.is_deleted() and not deleted: continue
            if t.is_completed() and not completed: continue
            if t.is_active() and not active: continue
            if filter not in t.description: continue

            if filter_project:
                for p in [self._project_lookup(p) for p in t.projects]: 
                    if filter_project in p.description: stop = False
                if stop: continue

            if projects: 
                projects_names = [p.name for p in projects]
                for p in t.projects: 
                    if p in projects_names: stop = False
                if stop: continue
            if t.is_inprogress(): inprogress.append(t); continue

            tasks.append(t)


        if limit < len(tasks): tasks = tasks[:limit]

        if waiting:
            if one_line:
                print.add((_c.orange + '{:^5} {:^10} {:^4} {:^5} {:^7} - {}' + _c.reset).format(
                        'ID', 'due-date', 'P-ID', 'status', 'I/U', 'description'))

                for t in scheduled:
                    print.add((_c.green + '{:5} {:10} {:^4}  {:^4}  {:>3}/{:<3} - ' + _c.reset).format(
                        t.name, t.due, t.project, t.status, t.importance, t.urgency) + t.description.splitlines()[0])

            else:
                for t in tasks:
                    out = (_c.orange + 'ID: {:5}\nstatus: {:^6}\ndue-date: {:10}\nI/U: {:>3}/{:<3}' + _c.reset).format(
                        t.name, t.status, t.due, t.importance, t.urgency)
                    out += '\n   ' + t.description.replace('\n', '\n   ')
                    print.add(out)

        
            print.empty(); return


        if info and one_line:
            if info > 2:
                print.add((_c.orange + '{:^5} {:^10} {:^4} {:^5} {:^7} - {}' + _c.reset).format(
                    'ID', 'due-date', 'P-ID', 'status', 'I/U', 'description'))

                for t in inprogress:
                    print.add((_c.green + '{:5} {:10} {:^4}  {:^4}  {:>3}/{:<3} - ' + _c.reset).format(
                        t.name, t.due, t.project, "doing", t.importance, t.urgency) + t.description.splitlines()[0])
                
                if inprogress: print.add("")

                for t in tasks:
                    print.add((_c.green + '{:5} {:10} {:^4}  {:^4}  {:>3}/{:<3} - ' + _c.reset).format(
                        t.name, t.due, t.project, t.status, t.importance, t.urgency) + t.description.splitlines()[0])


            elif info == 2:
                print.add((_c.orange + '{:^4} {:^7} {:4} - {}' + _c.reset).format(
                    'ID', 'I/U', 'P-ID', 'description'))

                for t in inprogress:
                    print.add((_c.green + '{:4} {:>3}/{:<3} {:^4} - ' + _c.reset).format(
                        t.name, t.importance, t.urgency, t.project) + t.description.splitlines()[0])
                
                if inprogress: print.add("")

                for t in tasks:
                    print.add((_c.green + '{:4} {:>3}/{:<3} {:^4} - ' + _c.reset).format(
                        t.name, t.importance, t.urgency, t.project) + t.description.splitlines()[0])

            elif info == 1:
                print.add((_c.orange + '{:^4} {:^7} - {}' + _c.reset).format(
                    'ID', 'I/U', 'description'))

                for t in inprogress:
                    print.add((_c.green + '{:4} {:>3}/{:<3} - ' + _c.reset).format(
                        t.name, t.importance, t.urgency) + t.description.splitlines()[0])
                
                if inprogress: print.add("")

                for t in tasks:
                    print.add((_c.green + '{:4} {:>3}/{:<3} - ' + _c.reset).format(
                        t.name, t.importance, t.urgency) + t.description.splitlines()[0])
                    

        elif info and not one_line:
            if info > 2:

                for t in inprogress:
                    out = (_c.orange + 'ID: {:5}\nstatus: {:^6}\ndue-date: {:10}\nI/U: {:>3}/{:<3}' + _c.reset).format(
                        t.name, t.status, t.due, t.importance, t.urgency)
                    out += '\n   ' + t.description.replace('\n', '\n   ')
                    print.add(out)

                if inprogress: print.add("")

                for t in tasks:
                    out = (_c.orange + 'ID: {:5}\nstatus: {:^6}\ndue-date: {:10}\nI/U: {:>3}/{:<3}' + _c.reset).format(
                        t.name, t.status, t.due, t.importance, t.urgency)
                    out += '\n   ' + t.description.replace('\n', '\n   ')
                    print.add(out)

            elif info == 2:

                for t in inprogress:
                    out = (_c.orange + 'ID: {:5}\nI/U: {:>3}/{:<3}\nstatus: {:^6}' + _c.reset).format(
                        t.name, t.importance, t.urgency, t.status)
                    out += '\n   ' + t.description.replace('\n', '\n   ')
                    print.add(out)

                if inprogress: print.add("")

                for t in tasks:
                    out = (_c.orange + 'ID: {:5}\nI/U: {:>3}/{:<3}\nstatus: {:^6}' + _c.reset).format(
                        t.name, t.importance, t.urgency, t.status)
                    out += '\n   ' + t.description.replace('\n', '\n   ')
                    print.add(out)

            elif info == 1:

                for t in inprogress:
                    out = (_c.orange + 'ID: {:5}\nI/U: {:>3}/{:<3}' + _c.reset).format(
                        t.name, t.importance, t.urgency)
                    out += '\n   ' + t.description.replace('\n', '\n   ')
                    print.add(out)

                if inprogress: print.add("")

                for t in tasks:
                    out = (_c.orange + 'ID: {:5}\nI/U: {:>3}/{:<3}' + _c.reset).format(
                        t.name, t.importance, t.urgency)
                    out += '\n   ' + t.description.replace('\n', '\n   ')
                    print.add(out)


        elif not info and one_line:
            print.add(_c.orange + '  ID - description' + _c.reset)

            for t in inprogress:
                out = (_c.green + '{:4} - ' + _c.reset).format(
                    t.name) + t.description.splitlines()[0] 
                print.add(out)

            if inprogress: print.add("")

            for t in tasks:
                out = (_c.green + '{:4} - ' + _c.reset).format(
                    t.name) + t.description.splitlines()[0] 
                print.add(out)


        elif not info and not one_line:

            for t in inprogress:
                out = ((_c.green + 'ID: {}' + _c.reset).format(t.name))
                out += '\n   ' + t.description.replace('\n', '\n   ')
                print.add(out)

            if inprogress: print.add("") 

            for t in tasks:
                out = ((_c.green + 'ID: {}' + _c.reset).format(t.name))
                out += '\n   ' + t.description.replace('\n', '\n   ')
                print.add(out)

        print.empty()


    def stats(self):

        active_projects  = [p for p in self.projects if self._is_project_active(p)]
        inprogress_tasks = [t for t in self.tasks if t.is_inprogress()]
        active_tasks     = [t for t in self.tasks if t.is_active()]
        completed_tasks  = [t for t in self.tasks if t.is_completed()]
        
        print.add('Projects', color='orange')
        print.add(f'\tactive: {len(active_projects)}')
        print.add(f'\tcompleted: {len(self.projects)}')

        print.add('Tasks', color='orange')
        print.add(f'\tin progress: {len(inprogress_tasks)}, {round(sum(t.time for t in inprogress_tasks), 1)} [h]')
        print.add(f'\tactive: {len(active_tasks)}, {round(sum(t.time for t in active_tasks), 1)} [h]')
        print.add(f'\tcompleted: {len(completed_tasks)}, {round(sum(t.time for t in completed_tasks), 1)} [h]')

        print.empty()

    
    def priority(self):
        self.projects.sort(key=lambda p: p.name, reverse=True)
        self.projects.sort(key=lambda p: p.importance, reverse=True)
        self.projects.sort(key=lambda p: p.urgency, reverse=True)
        projects = [p for p in self.projects if self._is_project_active(p)]

        if not projects: print('No active projects in the todo list'); return
        if len(projects) == 1: 
            print.add("P-ID priority - description")
            print.add(f"{projects[0].name:4}    1    - {projects[0].description.splitlines()[0]}")

        else:
            p0 = projects[0]
            p1 = projects[1]

            u0, u1 = max(p0.urgency, 0.0001), max(p1.urgency, 0.0001)

            pt0, pt1 = u0/(u0+u1), u1/(u0+u1)

            print.add("P-ID priority - description", color='orange')

            if pt0 > pt1:
                print.add(f"{p0.name:4}    {round(pt0, 1)}   - {p0.description.splitlines()[0]}")
                print.add(f"{p1.name:4}    {round(pt1, 1)}   - {p1.description.splitlines()[0]}")
            else:
                print.add(f"{p1.name:4}    {round(pt1, 1)}   - {p1.description.splitlines()[0]}")
                print.add(f"{p0.name:4}    {round(pt0, 1)}   - {p0.description.splitlines()[0]}")

        print.empty()

    
    def _is_project_active(self, p):
        project_tasks = []
        for t in self.tasks:
            if p.name in t.projects:
                project_tasks.append(t)
        
        if not project_tasks: return True   # Consider projects with no tasks as active
        project_tasks = [t for t in project_tasks if t.is_active()]

        return len(project_tasks) > 0   # Or projects with active tasks

    
    def _is_project_completed(self, p):
        return not self._is_project_active(p)


    def list_projects(self, sort, limit, active, completed, filter, info):

        if sort in ['importance', 'I']: 
            self.tasks.sort(key=lambda p: p.name, reverse=True)
            self.projects.sort(key=lambda p: p.urgency, reverse=True)
            self.projects.sort(key=lambda p: p.importance, reverse=True)

        elif sort in ['creation', 'C']:
            self.tasks.sort(key=lambda p: p.name, reverse=True)

        else:
            self.tasks.sort(key=lambda p: p.name, reverse=True)
            self.projects.sort(key=lambda p: p.importance, reverse=True)
            self.projects.sort(key=lambda p: p.urgency, reverse=True)

        projects = []
        if filter: completed = True
        for p in self.projects:
            p.status = Project.ACTIVE if self._is_project_active(p) else Project.COMPLETED

            if p.is_completed() and not completed: continue
            if p.is_active() and not active: continue
            if filter not in p.description: continue

            projects.append(p)

        if limit < len(projects): projects = projects[:limit]

        if info > 2:
            print.add((_c.orange + 'P-ID  {:9} {:^10} {:^7} - {}' + _c.reset).format(
                'status', 'due-date', 'I/U', 'description'))

            for p in projects:
                print.add((_c.green + '{:5} {:9} {:10} {:>3}/{:<3} - ' + _c.reset + '{}').format(
                    p.name, p.status, p.due, p.importance, p.urgency, p.description.splitlines()[0]))

        elif info == 2:
            print.add((_c.orange + 'P-ID {:^10}  {:^7} - {}' + _c.reset).format(
                'due-date', 'I/U', 'description'))

            for p in projects:
                print.add((_c.green + '{:5} {:10} {:>3}/{:<3} - ' + _c.reset + '{}').format(
                    p.name, p.due, p.importance, p.urgency, p.description.splitlines()[0]))

        elif info == 1:
            print.add((_c.orange + 'P-ID  {:^10} - {}' + _c.reset).format(
                'due-date', 'description'))

            for p in projects:
                print.add((_c.green + '{:5} {:10} - ' + _c.reset + '{}').format(
                    p.name, p.due, p.description.splitlines()[0]))

        elif info == 0:
            print.add((_c.orange + 'P-ID - {}' + _c.reset).format('description'))

            for p in projects:
                print.add((_c.green + '{:4} - ' + _c.reset + '{}').format(p.name, p.description.splitlines()[0]))


        print.empty()

TodoList = decorate_class(TodoList, debugger(logger, 'TodoList'))