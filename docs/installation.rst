Installation
------------

**blargh** is in early-beta phase:

- core functionality works
- there are no serious known bugs
- tests were performed only on a single environment (Ubuntu 18.10 + python3.6.7)
- backward incompatible changes are expected in the future

Installation via pip: ::

    pip install blargh

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
