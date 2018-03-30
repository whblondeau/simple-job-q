# simple-job-q

**TL;DR: A reliable job queue using the linux file system and CLI, with Python
orchestration.**

## Using traditional practices to implement a high-reliability job queue.
Intended for use with the unix/linux filesystem and command line. Orchestrated
with Python, favoring subprocess execution of `bash` commands over native Python
equivalents -- within reason. 
  - No, this is not Pythonic. Pythonistas like to favor implementations that
    run on all platforms. This is not that.
  - This is purposeful. This design favors being as promptly comprehensible
    to linux-savvy IT and DevOps people as possible.
  - Anyone wishing to adapt this for Windows PowerShell or something should
    have a pretty short walk.
  - Similarly, those who favor non-`bash` unix shells would find this easy to
    adapt.
  - Fork away, folks.


## Unit of Work
A Unit of Work, or **UOW**, is a text file describing a job to be done.

A UOW contains:
  - A **timestamp** on the first line, stating when the UOW was first enqueued;
  - A **header**, which contains any information necessary to define the
    specific job to be done;
  - A **status**, which provides a single summary entry describing the outcome
    of the job;
  - A **log**, used to store any desired process output generated during
    the job.

The named parts of the UOW are identified by title lines, conventionally
represented as

`==== UNIT OF WORK` for the header

Contents are stated in `NAME :: CONTENT` form, one named item per line

`==== STATUS` for the status entry

Content will be a single line

`==== JOB LOG` for the logged output of executed jobs

Blank lines are ignored. IMO you're foolish if you don't use them to make the
content/heading associations more readable; but they are not mandatory.


## Queue design
The queue is implemented as directories with conventional names:

- **(simple job root):** This directory contains the entire installation.
  It's self-contained: it can have any desired name, and can be located 
  wherever desired. 

  This top directory contains:

  - **Executable and config files:**
    - `monitor.py`
    - `config.txt` (optional, for overriding defaults set in `monitor.py`)
    - `monitor_reads` (the default file for incoming messages, can be 
      overridden in `config.txt`)
    - `monitor_says` (the default file for outgoing messages, can be 
      overridden in `config.txt`)

  - **Queue operational directories** (these can be renamed in `config.txt`)**:**
    - **wait-q:** The principal job queue. 
    - **priority-q:** A queue for high-priority jobs. UOWs in `wait-q` will not
      be processed unless `priority-q` is empty.
    - **currently-executing:** A container for a **single** UOW, which is about
      to be executed, is currently being executed, or has completed execution.
    - **done-q:** A queue for successfully completed UOWs.
    - **error-q:** A queue for UOWs that completed, but with an error condition
      indicating an unsuccessful attempt.
    - **fail-q:** A queue for UOWs that did not complete. "Fail", in this case,
      means "Failed in an out-of-context way." (Example: network outage during job
      execution.)

  - **Non-queue operational/convenience directories:**
    - **trash:** A discard directory for discovered files that are
      not valid UOWs.
    - **archive:** a directory for storing UOWs that are required only for 
      historical purposes.



The queues have the following design constraints:
  - No subdirectories.
  - A single file with the reserved name "README" can exist in each of the
    directories. The Monitor will ignore that file. The Monitor will also
    enforce the there-can-be-only-one rule: it will delete all README files
    except the most recent one.


## The Monitor
This is the active executing entity in simple-job-q. It assumes 
responsibility for:
  - Reading incoming messages;
  - Writing outgoing mssages;
  - Tracking the existence and positions of UOW files in the directories;
  - Validating those files;
  - Modifying and moving the files as necessary;
  - Launching the jobs described by the UOWs;
  - Reporting status of enqueued UOWs;
  - Reporting status of active job processes.

The Monitor is implemented in `monitor.py`

## Logic of Monitor Operation

### Wake up.
This happens after a sleep period that is set to a configurable value in 
seconds. (If you need sleep periods shorter than a second, you probably want
something other than `simple-job-q`.) The envisioned sleep period is on the
order of 15 seconds for a reasonably responsive system.

### Check incoming messages.
Incoming messages can affect the run state of the Monitor. Therefore, they are checked first.

### Survey the system state.
This state is specifically the ahistorical snapshot Queue State:
  - What files are in which folders?
  - What are the line-by-line contents of the files?

### Move files as necessary.
There are four kinds of movement that the Monitor performs:
  - Move discovered files that are not valid UOWs into `trash`.
  - Move superfluous `README` files into `trash` (favoring the newest.)
  - Move a UOW whose process has exited or timed out from `currently-executing`
    to either
      - `done-q`,
      - `error-q`, or
      - `fail-q`. The determination is based on file content and the special
        exclusion for "stuck" processes that time out.
  - Move a UOW from `priority-q` or `wait-q` to a vacant `currently-executing`.

### Edit files as necessary.
Files in the `simple-job-q` can be edited in specific ways for specific 
reasons:
  - A UOW in `wait-q` or `priority-q` that has no timestamp will be
    timestamped.
  - A UOW whose status changes will have its `==== STATUS` content updated.
    Note that this does _not_ entail adding superfluous entries that could be deduced by 
    queue position or other inexpensive computation.

### Launch A Job as indicated.
If a valid UOW exists in `currently-executing`, and there is no process of the
configured job type running, and the UOW has not been run, the Monitor
will launch the job described by the UOW.

The job program will be launched and piped to the linux command `tee`, which
in turn will be instructed to append content to the UOW file itself.

Some points about this:

**Color:** Any existing color codes embedded in the program will be preserved.
Color is often a valuable property of output. The color can be reproduced
at will by running `cat` against the UOW.

Of course, embedded color codes make output difficult to sight-read. There
are several ways of creating a copy with color codes stripped out: You
can run a `sed` command that removes them; you can write a text hacking
utility in Perl, Python, or whatever; or -- and this is the most elegantly
simple and foolproof -- you can _`cat` the file, copy the output from
the terminal, and paste it into a text editor._ 

This last point underscores a design goal of `simple-job-q`: _Don't do
stuff that people can do already without undue burden._ 

### Post current status.
This is optional, but way too handy. Stand up a description of `simple-job-q`'s
snapshot status, and park it someplace (the exact place is configurable).

One likely place to post a digest of the status would be in a web server, as HTML
with drill-down links for detail information.

### Go to sleep.

That's all.


## Messaging
`simple-job-q` supports a limited facility for practical message traffic.

**Incoming messages** are commands that instruct the Monitor to perform
a certain action. There is a defined set of operations listed in `monitor.py`,
each with:
  - a message keyword,
  - a human-readable description of the Monitor's response,
  - a reference to an implementing operation function.

The Monitor will report via outgoing messages when it finds incorrect content
in incoming messages, and will thn remove that incorrect content.

The Monitor deletes incoming messages that it has acted upon.

**Outgoing messages** are notifications and responses written by the Monitor.

All outgoing messages are timestamped.

Messages are appended to files, one for incoming messages, one for outgoing. The
file pathnames are configured in `monitor.py` and (optionally) overriddden in
`config.txt`.

## Operations
`simple-job-q` is intended to be largely hands-free; but there are some actions
that are manual and straightforward.

### Running the monitor
It's recommended that the Monitor be controlled by `systemctl` in practical
applications.

### Submitting a job
1. Create the UOW textfile to define the job. The filename is not constrained; the strong recommendation is to use a naming convention that maximizes clarity (e.g., give it the name of the corresponding ticket in your ticket management system.)
2. Drop the UOW into `wait-q`, or -- if you _really_ need to push the priority -- `priority-q`.
3. Ensure that the monitor is running.
4. Check the outgoing messages file for any notice that the job has been started, completed, etc.
5. For a recap of the job's specifics, `cat` the UOW in `done-q`, `error-q`, or `fail-q` as appropriate.
