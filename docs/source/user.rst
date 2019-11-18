User
======

Token
------
**URL** : /user/token/

**Method** : POST

**Auth required** : YES

**Permissions required** : None

POST Data Example
~~~~~~~~~~~~~~~~~~
.. code-block:: json

    {"email": "user@uw.edu", "password": "supersecret"}


POST Success Response
~~~~~~~~~~~~~~~~~~~~~~~~~

**Code** : 201 OK

**Response example**:

.. code-block:: json

    {"token":"supersecrettoken"}


POST Error Response
~~~~~~~~~~~~~~~~~~~~~

**Code** : 400 Bad Request

**Response example:**

.. code-block:: json

    {"non_field_errors":["Unable to authenticate with provided credentials"]}

Notes
~~~~~~

* Account must be created before reqeusting token
