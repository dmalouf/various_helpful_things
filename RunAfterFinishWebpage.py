#!/usr/bin/python3

"""
This script is a webpage that fires off another Python script in the background, letting the user
move on without stopping background task.

This was a little project that was based on my need to fire-off a process that was not bound to a
web-user staying on the webpage.

Assumes this file is an 'endpoint' (ex. POST /run_after_finish_webpage.py) and that there is another
Python script (e.g. 'backgroundTask.py') in 'this' file's folder that will be run as a subprocess
even after 'this page' is done sending the end-of-request to the user.

Assumes, both on the very first line and also in the `args` creationg below, that the Python
executable is located at: /usr/bin/python3

"""

import subprocess
import os

python_file_to_run = "backgroundTask.py"

# Without this, anything that goes to the browser will just throw a 500
print("Content-type: text/html\r\n\r\n")

# Gather data from <form>, query-string, etc. for passing along via CLI
# - VITAL that these are sanitized!
some_args = "something here"

# Setup the executable
the_executabe = f'{os.getcwd()}{python_file_to_run}'
args = ['/usr/bin/python3', the_executable, some_arg]

# Start sub-process
variable_for_debugging = subprocess.Popen(args)

# Do other things here if/as needed

