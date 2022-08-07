from biumsputils import filesIO
from biumsputils.decorators import debugger, decorate_module, decorate_class
from biumsputils.logger import logger
from biumsputils.print import print
from biumsputils.editor_input import editor_input
from biumsputils.git_wrapper import GitWrapper
from biumsputils.fatal_error import fatal_error
from biumsputils.input_validation import *
from biumsputils.colorcodes import Colorcodes
from datetime import datetime

_c = Colorcodes()
#filesIO = decorate_module(filesIO, debugger(logger, 'filesIO'))

def get_valid_description(message: str, initial_message=''):
    if message is None:
        message = editor_input(initial_message=initial_message)
    
    if message == '':
        fatal_error('description cannot be empty')

    message.strip()
    if not message.endswith('\n'):
        message += '\n'
        
    return message

def now(date=False):
    if date:
        return datetime.now()
    else:
        return datetime.now().strftime(r"%Y-%m-%d")

def never():
    return "2998-12-31"

def num2str(x):
    x = str(x)
    z = 4 - len(x)

    if z < 0:
        print('Fatal Error: you reached 10000 tasks. Need to increase names')

    return '0'*z + x

def diff_dates(d1, d2):
    d1 = datetime.strptime(d1, r"%Y-%m-%d")
    d2 = datetime.strptime(d2, r"%Y-%m-%d")

    return (d1 - d2).days

def validate_date(date):        
    if date < datetime.now(): fatal_error('date cannot be in the past')
    fatal_error(f'invalid date {date}')
