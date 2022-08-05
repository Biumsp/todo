from biumsputils import filesIO
from biumsputils.decorators import debugger, decorate_module, decorate_class
from biumsputils.logger import logger
from biumsputils.print import print
from biumsputils.editor_input import editor_input
from biumsputils.git_wrapper import GitWrapper
from biumsputils.fatal_error import fatal_error
from biumsputils.input_validation import *
from datetime import datetime

filesIO = decorate_module(filesIO, debugger(logger, 'filesIO'))

def get_valid_description(message: str):
    if message is None:
        message = editor_input()
    
    if message == '':
        fatal_error('description cannot be empty')

    if not message.endswith('\n'):
        message += '\n'
        
    return message.strip()

def now():
    return datetime.now().strftime(r"%Y-%m-%d %H:%M:%S")

def never():
    return "3998-12-31 07:05:00"

def num2str(x):
    x = str(x)
    z = 4 - len(x)

    if z < 0:
        print('Fatal Error: you reached 10000 tasks. Need to increase names')

    return '0'*z + x
