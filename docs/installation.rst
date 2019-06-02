Installation
------------

Installation via pip: ::

    pip install blargh

**blargh** is in early-beta phase:

- core functionality works
- there are no serious known bugs
- tests were performed only on a single environment (Ubuntu 18.10 + python3.6.7)
- backward incompatible changes are expected in the future
- code quality is moderately good, but large part of the api reference is missing 
  and there are some extremaly ugly hotfixes here and there

Core part of the code has no requirements, but until internal imports are improved those are necesary:

- Flask
- flask-restful
- psycopg2

Development version `on GitHub <https://github.com/johny-b/blargh>`_: ::

    git clone git@github.com:johny-b/blargh.git
    
Running tests: ::

    pytest tests

Running tests also for PGStorage (:doc:`/storage`) requires passing psycopg2-style connection string: ::

    PGS_CONNSTR='database_address' pytest tests
    # e.g.
    PGS_CONNSTR='dbname=test port=5432' pytest tests
