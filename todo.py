from todo_utilities import print
from todo_utilities import excludes, validate, never
from todo_utilities import logger
from storage import Storage
import os, click, sys

# # Read configurations
# HOME = os.path.expanduser('~')
# CONFIG = os.path.join(HOME, '.myconfig/photos/photos_config.json') 

# CONFIG = filesIO.read(CONFIG, loads=True)
# PATTERNS = CONFIG['patterns']   # {"pattern": "source"}
# LABELS = CONFIG['labels']       # {"source" : ["labels"]}
# #NO_TIME_SOURCES = CONFIG['no_time_sources'] # ["sources"]

# logger.set_state_debug()
# logger.activate_IO()
# print.auto_indent()
# print.lines_step()

STORAGE_PATH = os.path.expanduser('~/.todo_storage')
storage = Storage(STORAGE_PATH)

DEFAULT_SORT = 'urgency'
DEFAULT_INFO = 0
DEFAULT_ONELINE = True

@click.group(invoke_without_command=True)
@click.option('--logging-info', is_flag=True, help='Set logging to info', hidden=True)
@click.option('--logging-debug', is_flag=True, help='Set logging to debug', hidden=True)
@click.option('--logging-io', is_flag=True, help='Activate I/O logging', hidden=True)
@click.option('--indent', is_flag=True, help='Nested indentation', hidden=True)
@click.option('--sort', '-s', default=DEFAULT_SORT, type=click.Choice(['urgency', 'U', 'importance', 'I']))
@click.option('--project', '-p', multiple=True, help='Project to filter by')
@click.option('--info', '-i', default=DEFAULT_INFO, count=True, help='Show info')
@click.option('--active / --no-active', '-a / -A', is_flag=True, default=True, help='Include active tasks')
@click.option('--completed / --no-completed', '-c / -C', is_flag=True, default=False, help='Include completed tasks')
@click.option('--deleted / --no-deleted', '-d / -D', is_flag=True, default=False, help='Include deleted tasks')
@click.option('--limit', '-l', default=5, help='Limit the number of results')
@click.option('--no-limit', '-L', is_flag=True, help='Show all the results')
@click.option('--one-line / --multi-line', '-o / -O', is_flag=True, default=DEFAULT_ONELINE, help='Short output')
def cli(logging_info, logging_debug, logging_io, indent, sort,
		project, active, completed, deleted, limit, no_limit, info, one_line):

	# Validate input
	validate(excludes(logging_debug, logging_info), 'can only set one info level')

	project = list(set(project))
	if no_limit: limit = 10000

	# Set logging state
	if logging_debug: logger.set_state_debug()
	elif logging_info: logger.set_state_info()    

	if logging_io: logger.activate_IO()
	if indent: print.auto_indent()

	storage.list(sort, project, active, completed, deleted, limit, info, one_line)


@cli.command(no_args_is_help=True)
@click.option('--project', '-p', multiple=True, help='Project the task belongs to')
@click.option('--new-project', '-n', multiple=True, help='Create new project')
@click.option('--description', '-d', type=str, help='Task description')
@click.option('--after', '-a', multiple=True, help='The tasks it depends on')
@click.option('--before', '-b', multiple=True, help='The tasks depending on this task')
@click.option('--due', default=never(), help='Due date')
@click.option('--git', '-g', 'commit', type=str, help='Git commit message')
def add(project, new_project, description, after, before, due, commit):

	# Validate input
	project 	 = list(set(project))
	new_project  = list(set(new_project))
	after 		 = list(set(after))
	before 		 = list(set(before))

	storage.add(project, new_project, description, after, before, due, commit)


@cli.command()
@click.option('--sort', '-s', default=DEFAULT_SORT, type=click.Choice(['urgency', 'U', 'importance', 'I']))
@click.option('--limit', '-l', default=5, help='Limit the number of results')
@click.option('--no-limit', '-L', is_flag=True, help='Show all the results')
@click.option('--active / --no-active', '-a / -A', is_flag=True, default=True, help='Include active projects')
@click.option('--completed / --no-completed', '-c / -C', is_flag=True, default=False, help='Include completed projects')
def prog(sort, limit, no_limit, active, completed):

	# Validate input
	if no_limit: limit = 10000
	
	storage.list_projects(sort, limit, active, completed)


@cli.command(no_args_is_help=True)
@click.argument('task-id', type=int, required=True)
@click.option('--git', '-g', 'commit', type=str, help='Git commit message')
def done(task_id, commit):

	storage.done(task_id, commit)


@cli.command(no_args_is_help=True)
@click.argument('task-id', type=int, required=True)
@click.option('--git', '-g', 'commit', type=str, help='Git commit message')
def restore(task_id, commit):

	storage.restore(task_id, commit)


@cli.command(no_args_is_help=True)
@click.argument('task-id', type=int, required=True)
@click.option('--yes', is_flag=True, callback=lambda c, p, v: sys.exit(0) if not v else None, expose_value=False, prompt='Are you sure?')
@click.option('--git', '-g', 'commit', type=str, help='Git commit message')
def delete(task_id, commit):

	storage.delete(task_id, commit)


@cli.command(no_args_is_help=True)
@click.argument('task-id', type=int, required=True)
@click.option('--project', '-p', multiple=True, help='Add existing project to task')
@click.option('--new-project', '-n', multiple=True, help='Create new project and add it to task')
@click.option('--after', '-a', multiple=True, help='The tasks it depends on')
@click.option('--before', '-b', multiple=True, help='The tasks depending on this task')
@click.option('--due', '-d', type=str, help='Due date')
@click.option('--override', '-O', is_flag=True, help='Override existing info')
@click.option('--git', '-g', 'commit', type=str, help='Git commit message')
def edit(task_id, project, new_project, after, before, due, override, commit):
	
	# Validate input
	project 	 = list(set(project))
	new_project  = list(set(new_project))
	after 		 = list(set(after))
	before 		 = list(set(before))

	validate(excludes(after, project), 'cannot modify projects and reference at the same time')
	validate(excludes(before, project), 'cannot modify projects and reference at the same time')
	validate(excludes(after, new_project), 'cannot modify projects and reference at the same time')
	validate(excludes(before, new_project), 'cannot modify projects and reference at the same time')
	validate(excludes(due, new_project), 'cannot modify projects and due-date at the same time')
	validate(excludes(due, project), 'cannot modify projects and due-date at the same time')
	validate(excludes(due, after), 'cannot modify precedence and due-date at the same time')
	validate(excludes(due, before), 'cannot modify precedence and due-date at the same time')

	storage.edit(task_id, project, new_project, after, before, due, override, commit)


@cli.command()
def push():
    '''Push the storage to remote'''
    
    storage.git.push()


@cli.command()
def pull():
    '''Pull the storage from remote'''
    
    storage.git.pull()
