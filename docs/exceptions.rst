.. _exceptions:

Exceptions
==========

Structure
---------

In **blargh** exceptions are used internally to end processing of each request that
has to fail. In looks more or less like this:

.. code-block:: python

    class Internals:
        def process_data(data):
            if Internals.invalid_data(data):
                raise SomeException(msg="invalid data")
            return 200, {'result': 'success'}
    
    class Api:
        def make_request(data):
            try:
                processed_data = Internals.process_data(data)
                return 200, processed_data
            except SomeException as e:
                return e.status, e.details

    #   and our final user call is processed 
    Api.make_request({'some': data})

Contents of :code:`blargh.exceptions`:

::
                                            
    Error
      ProgrammingError
      ServerError
        e500
        TransactionConflictRetriable
      ClientError
        e400
          FieldDoesNotExists
          FieldIsReadonly
          FieldUpdateForbidden
          SearchForbidden
          BadParamValue
          BadFieldValue
        e401
        e404
        e422

Briefly speaking:

* ProgrammingError indicates that probably **blargh** user did something wrong
* ClientError indicates that application user did something wrong, and its descendants are related to specific kinds of mistakes
* e500 is raised when we encounter unexpected internal errors, e.g. disconnected database
* TransactionConflictRetriable is raised when request fails, but can be repeated (and :code:`Api.make_request` is called again).
  Its only raised by PGStorage and more detailed description is there.

Some of those exceptions are never raised by **blargh**, but could be raised by applications extening it.

List of error codes
-------------------

====== ====================== ======
Status Code                   Reason
====== ====================== ======
400    bad_request            Unknown client error. This could also be a generic database exception,
                              with details containing more information (e.g. 'ERROR:  null value in 
                              column "id" violates not-null constraint')
400    field_does_not_exists  User request references non-existent object field.
400    field_is_readonly      User tries to change a field he is not allowed to modify in a **direct** way.
400    field_update_forbidden User tries to change a field he is not allowed to modify in **any** way.
400    search_forbidden       User attempted to filter results (probably GET) by a field that shouldn't be used
                              for filtering, e.g. by a Calc field or my multi retaltional field.
400    bad_param_value        User sent invalid value of some url parameter, e.g. negative :code:`depth`, or invalid json for :code:`filter`.
400    bad_field_value        User tries to set field to an invalid value, e.g. to set 'one' to Scalar field with :code:`type_=int`
401    unauthorized           Missing authorization header
404    object_does_not_exist  Referenced object does not exists. 
                              This code for e.g. call :code:`PATCH cookie/1 {'jar': 7}`
                              might be returned both when cookie with :code:`id=1` is missing,
                              or for missing jar with :code:`id=7`.
422    unprocessable_entity   (this currently never happens)
500    unknown_error          We have no idea what failed. Probably an unexpected programming error.
500    server_error           Something failed internally, e.g. could not connect to the database.
====== ====================== ======



Exception interface
-------------------

.. code-block:: python
    
    from blargh.exceptions import Error
    try:
        raise Error(msg='something failed', what='no idea', where='also no idea')
    except Error as e:
        print(e.status)    # 500
        print(e.code)      # 'unknown_error'
        print(e.details)   # {'msg': 'something failed', 
                           #  'what': 'no idea', 
                           #  'where': 'also no idea'}
        
        #   this is by default returned as response body when request fails
        print(e.ext_data)  # {'error': {'code': 'unknown_error', 
                           #            'details': {'msg': 'something failed', 
                           #                        'what': 'no idea', 
                           #                        'where': 'also no idea'}
