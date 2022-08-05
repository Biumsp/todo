from todo_utilities import print
from todo_utilities import excludes, validate
from todo_utilities import logger
from storage import Storage
import os, click

# # Read configurations
# HOME = os.path.expanduser('~')
# CONFIG = os.path.join(HOME, '.myconfig/photos/photos_config.json') 

# CONFIG = filesIO.read(CONFIG, loads=True)
# PATTERNS = CONFIG['patterns']   # {"pattern": "source"}
# LABELS = CONFIG['labels']       # {"source" : ["labels"]}
# #NO_TIME_SOURCES = CONFIG['no_time_sources'] # ["sources"]

STORAGE_PATH = os.path.expanduser('~/.todo_storage')
storage = Storage(STORAGE_PATH)

@click.group(no_args_is_help=True)
@click.option('--logging-info', is_flag=True, help='Set logging to info')
@click.option('--logging-debug', is_flag=True, help='Set logging to debug')
@click.option('--logging-io', is_flag=True, help='Activate I/O logging')
@click.option('--indent', is_flag=True, help='Nested indentation')
def cli(logging_info, logging_debug, logging_io, indent):

	# Validate input
	validate(excludes(logging_debug, logging_info), 'can only set one info level')

	# Set logging state
	if logging_debug: logger.set_state_debug()
	elif logging_info: logger.set_state_info()    

	if logging_io: logger.activate_IO()
	if indent: print.auto_indent()


@cli.command()
@click.option('--projects', '-p', multiple=True, help='Projects the task belongs to')
@click.option('--new-projects', '-n', multiple=True, help='Create new projects')
@click.option('--description', '-d', help='Task description')
@click.option('--after', '-a', multiple=True, help='The tasks it depends on')
@click.option('--before', '-b', multiple=True, help='The tasks depending on this task')
@click.option('--git', '-g', 'commit', type=str, help='Git commit message')
def add(projects, new_projects, description, after, before, commit):

	# Validate input
	projects 	 = list(projects)
	new_projects = list(new_projects)
	after 		 = list(after)
	before 		 = list(before)

	storage.add(projects, new_projects, description, after, before, commit)
