from email.policy import default
from operator import sub
from todo_modules.utilities import print, filesIO
from todo_modules.utilities import excludes, validate, never, now
from todo_modules.utilities import logger
from todo_modules.todolist import TodoList
import os, click, sys

# logger.set_state_debug()
# logger.activate_IO()
# print.auto_indent()
# print.lines_step()

# Read configurations
MY_STATUS = os.getenv('MY_STATUS')
HOME = os.path.expanduser('~')


TODOLIST_PATH = os.path.join(HOME, '.todolist')
TODOLIST_PATH = os.path.join(TODOLIST_PATH, MY_STATUS)
CONFIG = os.path.join(TODOLIST_PATH, '.config.json')

todolist = TodoList(TODOLIST_PATH)
config = filesIO.read(CONFIG, loads=True, fail_silently=True)

if config == 'failed':
	DEFAULT_CONFIG = os.path.join(HOME, '.myconfig/todo/config.json')
	filesIO.copy(DEFAULT_CONFIG, CONFIG)
	config = filesIO.read(CONFIG, loads=True)

DEFAULT_SORT = config['default_sort']
DEFAULT_INFO = config['default_info']
DEFAULT_ONELINE = config['default_oneline']
DEFAULT_LIMIT = config['default_limit']


@click.group(invoke_without_command=True)
@click.pass_context
@click.option('--logging-info', is_flag=True, help='Set logging to info', hidden=True)
@click.option('--logging-debug', is_flag=True, help='Set logging to debug', hidden=True)
@click.option('--logging-io', is_flag=True, help='Activate I/O logging', hidden=True)
@click.option('--indent', is_flag=True, help='Nested indentation', hidden=True)
@click.option('--sort', '-s', default=DEFAULT_SORT, type=click.Choice(['urgency', 'U', 'importance', 'I', 'creation', 'C']), help='Order by')
@click.option('--project', '-p', multiple=True, help='Projects to filter by')
@click.option('--info', '-i', default=DEFAULT_INFO, count=True, help='Show info')
@click.option('--active / --no-active', '-a / -A', is_flag=True, default=True, help='Include active tasks')
@click.option('--completed / --no-completed', '-c / -C', is_flag=True, default=False, help='Include completed tasks')
@click.option('--deleted / --no-deleted', '-d / -D', is_flag=True, default=False, help='Include deleted tasks')
@click.option('--waiting / --no-waiting', '-w / -W', is_flag=True, default=False, help='Include scheduled tasks')
@click.option('--filter', '-f', default='', help='Filter by match in description')
@click.option('--limit', '-l', default=DEFAULT_LIMIT, help='Limit the number of results')
@click.option('--no-limit', '-L', is_flag=True, help='Show all the results')
@click.option('--one-line / --multi-line', '-o / -O', is_flag=True, default=DEFAULT_ONELINE, help='Short output')
def cli(ctx, logging_info, logging_debug, logging_io, indent, sort,
		project, active, completed, deleted, waiting, filter, limit, no_limit, info, one_line):
	'''See all your tasks'''

	# Validate input
	validate(excludes(logging_debug, logging_info), 'can only set one info level')

	# Manipulate input
	projects = list(set(project))
	if no_limit: limit = 10000

	# Set logging options
	if logging_debug: logger.set_state_debug()
	elif logging_info: logger.set_state_info()    
	if logging_io: logger.activate_IO()
	if indent: print.auto_indent()

	# List the task, if no sub-command is specified
	if ctx.invoked_subcommand is None:
		todolist.list(sort, projects, active, completed, deleted, waiting, filter, limit, info, one_line)


@cli.command(no_args_is_help=True)
@click.argument('project', type=int, required=True)
@click.option('--description', '-d', type=str, help='Task description')
@click.option('--after', '-a', multiple=True, help='The tasks it depends on')
@click.option('--before', '-b', multiple=True, help='The tasks depending on this task')
@click.option('--time', '-t', default=1., help='Estimated time to complete the task')
@click.option('--wait', '-w', default=None, type=click.DateTime(formats=[r'%Y-%m-%d', r'%m-%d']), help='Create the task on this date')
@click.option('--git', '-g', 'commit', type=str, help='Git commit message')
def add(project, description, after, before, time, wait, commit):
	'''Add a new task'''

	# Manipulate input
	after  = list(set(after))
	before = list(set(before))

	todolist.add(project, description, after, before, time, wait, commit)


@cli.command()
@click.option('--due', '-due', default=now(), type=click.DateTime(formats=[r'%Y-%m-%d', r'%m-%d']), help='Due date')
@click.option('--no-due', '-D', is_flag=True, help='No due date')
@click.option('--description', '-d', type=str, help='Project description')
@click.option('--importance', '-I', default=100, show_default=True, help='Project relative importance')
@click.option('--git', '-g', 'commit', type=str, help='Git commit message')
def addp(due, no_due, description, importance, commit):
	'''Create a new project'''

	# Manipulate input
	if no_due: due = never()

	todolist.add_project(due, description, importance, commit)


@cli.command()
@click.option('--sort', '-s', default=DEFAULT_SORT, type=click.Choice(['urgency', 'U', 'importance', 'I', 'creation', 'C']), help='Order by')
@click.option('--limit', '-l', type=int, default=100, help='Limit the number of results')
@click.option('--no-limit', '-L', is_flag=True, default=False, help='Show all the results')
@click.option('--active / --no-active', '-a / -A', is_flag=True, default=True, help='Include active projects')
@click.option('--completed / --no-completed', '-c / -C', is_flag=True, default=False, help='Include completed projects')
@click.option('--filter', '-f', default='', help='Filter by match in description')
@click.option('--info', '-i', default=DEFAULT_INFO, count=True, help='Show info')
def prog(sort, limit, no_limit, active, completed, filter, info):
	'''List all the projects'''

	# Manipulate input
	if no_limit: limit = 10000
	
	todolist.list_projects(sort, limit, active, completed, filter, info)


@cli.command(no_args_is_help=True)
@click.argument('task-id', type=int, required=True)
@click.option('--git', '-g', 'commit', type=str, help='Git commit message')
def doing(task_id, commit):
	'''Mark a task as in-progress'''

	todolist.doing(task_id, commit)


@cli.command(no_args_is_help=True)
@click.argument('task-id', type=int, required=True)
@click.option('--git', '-g', 'commit', type=str, help='Git commit message')
def done(task_id, commit):
	'''Mark a task as completed'''

	todolist.done(task_id, commit)


@cli.command(no_args_is_help=True)
@click.argument('task-id', type=int, required=True)
@click.option('--git', '-g', 'commit', type=str, help='Git commit message')
def restore(task_id, commit):
	'''Restore a completed or deleted task'''

	todolist.restore(task_id, commit)


@cli.command(no_args_is_help=True)
@click.argument('task-id', type=int, required=True)
@click.option('--yes', is_flag=True, callback=lambda c, p, v: sys.exit(0) if not v else None, expose_value=False, prompt='Are you sure?')
@click.option('--git', '-g', 'commit', type=str, help='Git commit message')
def delete(task_id, commit):
	'''Delete a task'''

	todolist.delete(task_id, commit)


@cli.command(no_args_is_help=True)
@click.argument('project-id', type=int, required=True)
@click.option('--yes', is_flag=True, callback=lambda c, p, v: sys.exit(0) if not v else None, expose_value=False, prompt='Are you sure?')
@click.option('--git', '-g', 'commit', type=str, help='Git commit message')
def deletep(project_id, commit):
	'''Delete a project'''

	todolist.delete(project_id, commit)


@cli.command(no_args_is_help=True)
@click.argument('task-id', type=int, required=True)
@click.option('--project', '-p', help='New project')
@click.option('--time', '-t', type=float, help='Estimated time to complete the task')
@click.option('--wait', '-w', default=None, type=click.DateTime(formats=[r'%Y-%m-%d', r'%m-%d', ]), help='Create the task on this date')
@click.option('--after', '-a', multiple=True, help='The tasks it depends on')
@click.option('--before', '-b', multiple=True, help='The tasks depending on this task')
@click.option('--override', '-O', is_flag=True, help='Override existing info')
@click.option('--git', '-g', 'commit', type=str, help='Git commit message')
def edit(task_id, project, time, wait, after, before, override, commit):
	'''Edit a task'''

	# Manipulate input
	after 	= list(set(after))
	before 	= list(set(before))

	# Check exclusions
	validate(excludes(after, project), 'cannot modify project and dependencies at the same time')
	validate(excludes(before, project), 'cannot modify project and dependencies at the same time')

	todolist.edit(task_id, project, time, wait, after, before, override, commit)


@cli.command(no_args_is_help=True)
@click.argument('project-id', type=int, required=True)
@click.option('--due', '-due', default=None, type=click.DateTime(formats=[r'%Y-%m-%d', r'%m-%d']), help='Due date')
@click.option('--delete-due', '-D', is_flag=True, help='Due date')
@click.option('--importance', '-I', type=int, help='Project relative importance')
@click.option('--git', '-g', 'commit', type=str, help='Git commit message')
def editp(project_id, due, delete_due, importance, commit):
	'''Edit a project'''
	
	# Validate input
	validate(excludes(delete_due, due), 'cannot modify and delete the due-date at the same time')

	# Manipulate input
	if delete_due: due = never()

	todolist.edit_project(project_id, due, importance, commit)


@cli.command(no_args_is_help=True)
@click.argument('task-id', type=int, required=True)
def show(task_id):
	'''Show all info about the task'''

	todolist.show(task_id)
	

@cli.command(no_args_is_help=True)
@click.argument('project-id', type=int, required=True)
def showp(project_id):
	'''Show all info about the project'''

	todolist.show_project(project_id)


@cli.command()
def priority():
	'''Compute projects priorities'''

	todolist.priority()


@cli.command(no_args_is_help=True)
@click.option('--date', '-d', default=None, type=click.DateTime(formats=[r'%Y-%m-%d', r'%m-%d']), help='Report date')
@click.option('--today', '-t', is_flag=True, help='Date is today')
@click.option('--yesterday', '-y', is_flag=True, help='Date is yesterday')
@click.option('--date-range', '-r', default=None, type=(click.DateTime(formats=[r'%Y-%m-%d', r'%m-%d']), click.DateTime(formats=[r'%Y-%m-%d', r'%m-%d', ])), help='Report date')
@click.option('--machine', '-m', is_flag=True, help='Machine-readable output format')
@click.option('--info', '-i', default=DEFAULT_INFO, count=True, help='Show info')
def report(date, today, yesterday, date_range, machine, info):
	'''Create a report of completed tasks on a specific date'''

	# Data validation
	validate(any([date, today, yesterday, date_range]), 'select at least one option')
	validate(excludes(today, yesterday), 'cannot select --today and --yesterday')
	validate(excludes(date_range, yesterday, today, date), '--date-range excludes the other options')

	# Data manipulation
	if today: date = now(date=True)
	if yesterday: print("--yesterday not yet implemented"); return
	if machine: print("--machine not yet implemented"); return
	if not date_range: date_range = (date, date)

	todolist.report(date_range, machine, info)


@cli.command()
def stats():
	'''Stats about the todo list'''

	todolist.stats()


@cli.command()
def push():
    '''Push the todolist to remote'''
    
    todolist.git.push()


@cli.command()
def pull():
    '''Pull the todolist from remote'''
    
    todolist.git.pull()
