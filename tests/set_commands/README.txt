Set Commands
========

This folder contains commands necessary to update Articles in the database.

Input Files (Path can be changed, saved as a global variable at top of class definition)
-----------

- tests/set_commands/manual_states/article_ids.csv: File containing a list of articles that should be saved. (Used in the save command)
- tests/set_commands/manual_states/original_state.csv: File containing the desired state of articles. (Used in set commands)

Output Files (Path can be changed, saved as a global variable at top of class definition)
-----------

- tests/set_commands/saved_states/article_stateXXX.csv: File containing the saved article states. (XXX is the user input in the save command)
- tests/set_commands/saved_states/incident_stateXXX.csv: File containing the saved incident states. (XXX is the user input in the save command)

Save Command
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Description
------------

The command takes the input list of articles and saves the current article state as well as the state of the related incidents.

Commands
--------

#. Display the help text::

    $ docker compose -f local.yml run --rm django python -m tests.set_commands savestate --help

#. Run save state::

    $ docker compose -f local.yml run --rm django python -m tests.set_commands savestate --stateNum {save_id: int}
