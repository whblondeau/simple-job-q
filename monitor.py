#!/usr/bin/python

'''This script controls UOW movement and editing; launches jobs; 
monitors the progress of jobs; monitors the state of the system.

While running, it will sleep for a configured interval when it has
no actions to perform.
'''


# -------------------------------------------------------------- COLORS

colors = {}
# ansi standard codes, with some nonconventional names
colors['nocolor'] = '\033[0m'
colors['red'] = '\033[31m'
colors['green'] = '\033[32m'
colors['dullyellow'] = '\033[33m'
# not legible on black screen background
colors['darkblue'] = '\033[34m'
colors['magenta'] = '\033[35m'
colors['cyan'] = '\033[36m'
# in cygwin, this is the default for uncolored text
colors['ltgray'] = '\033[37m'

# not standard ansi color codes: this syntax is an XTerm adaptation of ECMA-48 RGB coding.
colors['orange'] = '\033[38;2;255;111;0m'
colors['blue'] = '\033[38;2;64;127;255m'    # for visibility at commandline
colors['yellow'] = '\033[38;2;255;255;0m'
colors['brightwhite'] = '\033[38;2;255;255;255m'
colors['palegreen'] = '\033[38;2;162;255;192m'
colors['lightgreen'] = '\033[38;2;96;255;124m'
colors['lightred'] = '\033[38;2;255;112;192m'
colors['redorange'] = '\033[38;2;255;48;40m'    # for visibility at commandline
colors['lightredorange'] = '\033[38;2;255;96;70m'    # for visibility at commandline

colors['bold'] = '\033[1m'
colors['dim'] = '\033[2m'

# color convenience functions
def nocolor(thing):
    return colors['nocolor'] + str(thing) + colors['nocolor']

def red(thing):
    return colors['red'] + str(thing) + colors['nocolor']

def green(thing):
    return colors['green'] + str(thing) + colors['nocolor']

def dullyellow(thing):
    return colors['dullyellow'] + str(thing) + colors['nocolor']

def darkblue(thing):
    return colors['darkblue'] + str(thing) + colors['nocolor']

def magenta(thing):
    return colors['magenta'] + str(thing) + colors['nocolor']

def cyan(thing):
    return colors['cyan'] + str(thing) + colors['nocolor']

def ltgray(thing):
    return colors['ltgray'] + str(thing) + colors['nocolor']

def orange(thing):
    return colors['orange'] + str(thing) + colors['nocolor']

def blue(thing):
    return colors['blue'] + str(thing) + colors['nocolor']

def yellow(thing):
    return colors['yellow'] + str(thing) + colors['nocolor']

def brightwhite(thing):
    return colors['brightwhite'] + str(thing) + colors['nocolor']

def palegreen(thing):
    return colors['palegreen'] + str(thing) + colors['nocolor']

def lightgreen(thing):
    return colors['lightgreen'] + str(thing) + colors['nocolor']

def lightred(thing):
    return colors['lightred'] + str(thing) + colors['nocolor']

def redorange(thing):
    return colors['redorange'] + str(thing) + colors['nocolor']

def lightredorange(thing):
    return colors['lightredorange'] + str(thing) + colors['nocolor']

def bold(thing):
    return colors['bold'] + str(thing) + colors['nocolor']

def dim(thing):
    return colors['dim'] + str(thing) + colors['nocolor']




# -------------------------------------------------------------- FUNCTIONS


# -------- General Utils

def pretty_format(datastruct):
    pp = pprint.PrettyPrinter(indent=4)
    retval = pp.pformat(datastruct)

    return retval



# -------- CLI Functions

def cmdstring_to_cmdlist(cmdstring):
    '''Converts a CLI command to a list of lists.
    The outermost list is piped commands; each item in that list
    is of the command list form required by subprocess.Popen() 
    and its convenience wrappers.
    '''
    cmdstring = cmdstring.strip()
    if not cmdstring:
        return []

    retval = []
    # pipes need to be broken out
    cmdlist = cmdstring.split('|')

    for cmd in cmdlist:
        # remove leading and trailing space
        cmd = cmd.strip()
        # split on whitespace
        cmd = cmd.split()
        retval.append(cmd)

    return retval


def cmdlist_to_cmdstring(cmdlist):
    '''Converts a command list to a single CLI command character sequence.
    Reverses the action of `cmdstring_to_cmdlist` with normalized whitespace.
    '''
    retval = ' | '.join([' '.join(cmd) for cmd in cmdlist])

    return retval


def execute_cmdstring_shell(cmdstring):
    '''A convenience wrapper for the subprocess invocation of
    /bin/sh. NOT for use with untrusted input!
    '''
    output = ''

    output += subprocess.check_output(cmdstring, shell=True)

    return output


def execute_cmdstring(cmdstring):
    '''A convenience wrapper for the powerful but not easily readable
    subprocess pipe syntax. Does NOT invoke /bin/sh
    Accepts a CLI command string. 
    Returns the output of the final command.
    '''
    commands = cmdstring_to_cmdlist(cmdstring)

    if not commands:
        return ''

    # array of Popen commands we are piping
    command_procs = []  

    # the first command has a simpler syntax because 
    # it's not listening to a pipe
    command_procs.append(subprocess.Popen(commands[0], stdout=subprocess.PIPE))

    # the rest are all the same: their stdin is the previous proc's stdout pipe
    for cmd in commands[1:]:
        command_procs.append(subprocess.Popen(cmd, stdin=command_procs[-1].stdout, stdout=subprocess.PIPE))

    # Allow all but last proc to receive a SIGPIPE if successor exits.
    for proc in command_procs[:-1]:
        proc.stdout.close()

    # read output from stdout of the final proc in the pipeline
    retval = command_procs[-1].communicate()[0]

    return retval


def execute_cli(cmdstring, shell=False):
    '''Delegates to the lower-level subprocess wrappers. The `shell` 
    argument sends the command directly to /bin/sh without alteration,
    and should NEVER be set to True with untrusted content.
    '''
    if shell:
        return execute_cmdstring_shell(cmdstring)
    else:
        return execute_cmdstring(cmdstring)



# -------- File Utils


def file_lines(filepath):
    cmdstring = 'cat ' + filepath

    return execute_cli(cmdstring).split('\n')


def ls_dir(dirpath):
    '''Returns directory listing in LATEST-FIRST
    chronological order.
    '''
    cmdstring = 'ls -lt ' + dirpath

    return execute_cli(cmdstring).split('\n')



def parse_filename(infoline):
    '''Accepts a single line as generated by ls -l
    and returns the filename
    '''
    infoline = infoline.split()
    return infoline[-1]



def all_the_files(dirpath):
    '''This function snags all files in a directory and
    returns them as lists of lines. No subdirectories.
    '''
    if not dirpath.endswith('/'):
        dirpath += '/'
    retval = []
    filenames = ls_dir(dirpath)
    for filename in filenames:
        retval.append(file_lines(dirpath + filename))

    return retval



# -------- Timestamp Utils


def timestamp_seconds():
    '''Wrapper to clarify what's being done. This is seconds since the
    Epoch: 1 January, 1970, 0000 UTC. No timezone entanglement.
    '''
    return time.time()


def prepend_timestamp(uow_lines, eventname):
    '''This function inserts a timestamp line at the first line of the UOW.
    The timestamp line is 'timestamp: ' followed by the timestamp in seconds,
    followed one or more spaces and the eventname.
    '''
    timestamp_line = 'timestamp: ' + str(timestamp_seconds) + ' ' + eventname
    uow_lines.insert(0, timestamp_line)

    return uow_lines


def read_timestamp(uow_line):
    '''This function parses a timestamp entry, returning
    (timestamp, eventname), or an empty tuple if the line is not
    a valid timestamp.'''
    if not uow_line.strip():
        return tuple()

    if not uow_line.startswith('timestamp: '):
        return tuple()

    # discard boilerplate
    uow_line = ':'.join(uow_line.split(':')[1:])
    # divide on whitespace
    uow_line = uow_line.split()
    uow_line = [uow_line[0], ' '.join(uow_line[1:])]

    return tuple(uow_line)



# -------- Operations


def is_system_ready():
    '''This function returns True if the system is ready to launch
    another job from a UOW, False if not. Note that this applies
    to the external system, and is not to be used to evaluate
    this program's primary responsibilites, e.g. queue contents.
    (This function must be customized in order to do anything. Likely 
    checks include memory or volume space checks for heavyweight jobs; 
    system load average checks via `uptime`, and so on.)
    '''
    return True


def processes_already_running(procname):

    cmdstring = 'ps axo comm,etimes | grep ' + procname
    
    return execute_cli(cmdstring)




# -------- Message I/O

def write_entry(filehandle, msg):
    '''To simplify the code and to conventionalize format: with
    initial timestamp, colon, regularized whitespace, and
    newline usage to create blank line separation.
    '''
    filehandle.write('\n' + str(timestamp_seconds()) + ': ' + msg.strip() + '\n\n')



def write_outgoing_message(msg):

    msg_pathname = config['outgoing_message_filepath']

    filehandle = None
    # outgoing message file might or might not exist
    if not os.path.isfile(msg_pathname):
        # start a brand new file
        filehandle = open(msg_pathname, 'w+')
        write_entry(filehandle, 'Initializing new message file.')
    else:
        # set the file up for appending
        filehandle = open(outgoing_msg_pathname, 'a')

    write_entry(filehandle, msg)
    filehandle.close()



def read_incoming_messages():

    msg_pathname = config['incoming_message_filepath']

   # incoming message file might not exist.
    if not os.path.isfile(msg_pathname):
        # create the file and write the HOWTO
        filehandle = open(msg_pathname, 'w+')
        write_entry(filehandle, incoming_msg_howto)
        filehandle.close()

    else:
        filehandle = open(incoming_msg_pathname, 'r')
        incominglines = incoming_msgs.readlines()
        filehandle.close()

        indexes_read = []
        for indx, line in enumerate(incominglines):
            line = line.strip()
            if not line:
                # skip empty lines
                continue
            if line.startswith('#'):
                # skip comment lines
                continue

            # not a comment. We will want to remove it.
            indexes_read.append(indx)

            # is this a message?
            if len(line) > 10:
                line = line[:10] + '...'

            if line not in incoming_messages.keys():
                msg = 'Received invalid incoming message "' + line + '".'
                write_outgoing_message(msg)

            # OK, it's a real action
            write_outgoing_message('Received ' + line + ' request.')
            try:
                incoming_messages[line].action()
                write_outgoing_message(line + ' action completed.')
            except Exception as ex:
                write_outgoing_message()


 
def op_shutdown():
    msg = 'Monitor is shutting down...'
    # any graceful measures?
    write_outgoing_message(msg)
    exit(0)


def op_status():
    pass


def op_config():
    pp = pprint.PrettyPrinter(indent=4, depth=4)
    msg = pp.pretty_format(config)
    write_outgoing_message(msg)


def op_kill_job():
    pass


def op_help():
    write_outgoing_message(incoming_msg_howto)
    

def check_uow(uow_content):
    pass



def snapshot_queues():
    for qname in queue_names:
        dirname = config[qname]
        filestats = queue_names




def assess_and_act():
    '''This function looks at all of the managed state:
    UOWs and where they are. It takes action as needed.
    This is the basic heartbeat of the monitor.
    '''

    # is there a UOW in currently_executing?
    cmdstring = 'ls currently_executing'
    output = execute_cli(cmdstring).split('\n')
    for item in output:
        item = item.strip()
        if item == 'README':
            continue
        cmdstring = 'cat ' + item
        output = execute_cli(cmdstring).split('\n')









# -------------------------------------------------------------- CONSTANTS

usage = '''USAGE: 
'''

incoming_messages = {
    'SHUTDOWN'  : {'desc': 'Monitor performs clean shutdown and stops.',
        'action': op_shutdown,
    },
    'STATUS'    : {'desc': 'Monitor writes status to outgoing message file.',
        'action': op_status,
    },
    'CONFIG'    : {'desc': 'Monitor writes current config to outgoing message file.',
        'action': op_config,
    },
    'KILL JOB'  : {'desc': 'Monitor stops current job if/when possible.',
        'action': op_kill_job,
    },
    'HELP'      : {'desc': 'Monitor writes this HOWTO to outgoing message file.',
        'action': op_help,
    },
}

# TODO break out messages to render `incoming_messages` 'desc1
incoming_msg_howto = '''# MESSAGES FOR MONITOR HOWTO:
#  1. One message per line.
#  2. Empty lines are ignored.
#  3. Lines beginning with "#" are comments.
#  4. No inline comments: a "#" that is not at line start does not begin a comment.
#  5. Append your message to the end of the file.
#  6. Monitor will delete non-comment messages after reading them.
#  7. Monitor will write responses and status messages to the outgoing message file.
#  8. Monitor will not write to this file, except to set up this HOWTO.
#  9. If you send a bad or unrecognized message, check the outgoing message file.
# 10. Do not delete this HOWTO. If you do, see HELP.
# 11. These are the messages Monitor understands. YES, THEY ARE CASE-SENSITIVE.
#       SHUTDOWN        (Monitor performs clean shutdown and stops.)
#       FINISH          (Monitor exits after current job completes.)
#       STATUS          (Monitor writes status to outgoing message file.)
#       CONFIG          (Monitor writes current config to outgoing message file.)
#       KILL JOB        (Monitor stops current job if/when possible.)
#       HELP            (Monitor writes this HOWTO to outgoing message file.)
'''




# -------------------------------------------------------------- CONFIG DEFAULTS

queue_names = [
    'wait_q',
    'priority_q',
    'currently_executing',
    'done_q',
    'error_q',
    'fail_q',
]

qconfig = {
    # principal job queue
    'wait_q': 'wait-q',
    # dedicated queue for high-priority jobs
    'priority_q': 'priority-q',
    # location for currently executing UOW
    'currently_executing': 'currently-executing',
    # queue for successfully completed UOWs
    'done_q': 'done-q',
    # queue for UOWs that completed, but with an error
    # condition indicating an unsuccessful attempt
    'error_q': 'error-q',
    # queue for UOWs that did not complete
    'fail_q': 'fail-q',
    # nonqueue container for invalid files
    'trash': 'trash,',
}

config = {

    'sleep_time_seconds': 10,

    # these filepaths identify message-passing files to allow simple
    # communications between the monitor and external processes or people.
    # THESE ARE MESSAGE PASSING FILES, NOT LOGS.
    # the output flags file is wiped clean with every monitor restart.
    'outgoing_message_filepath': 'monitor_says',
    # any entry in the input flags file is deleted when the monitor reads it.
    # Note: this can be a symlink.
    'incoming_message_filepath': 'monitor_reads',

    # The jobs in this queue will be of various types. Here, as an example, 
    # is the case in which the commands launched by this queue are ansible
    # deploys. The timeout is in seconds; the ansible process in this example
    # should not take more than 30 minutes.
    'managed_procnames': [{'ansible', {'timeout': 30 * 60}}],

}




# -------------------------------------------------------------- EXECUTE

import subprocess
import os, os.path
import sys
import time
import pprint


# -------- initial setup: message I/O

# The Monitor's output

write_outgoing_message('Monitor starting up.')
# describe configuration
op_config()


# This script runs continuously until externally interrupted, or flagged to stop.

status = 'startup'
current_command = None
current_command_proc = None
current_uow = None

while true:
    # wake up and see what's going on

    # check for incoming messages. Execute any existing commands.
    read_incoming_messages()

    # is one running already? We will never launch if one is.
    for procname in config['managed_procnames']:

