Nslc
======

Authorization Header
---------------------
If endpoint Authorization is required set header::
.. code-block:: json

 {'Content-Type': 'application/json', 'Authorization': API_TOKEN}

Networks
--------

Endpoints
++++++++++

/nslc/networks
~~~~~~~~~~~~~~

**Method** : GET, POST, PUT

**Auth required** : YES

**Permissions required** : None

**GET Required** : None

**POST Required** 
 * code
 * name


POST Data Example
~~~~~~~~~~~~~~~~~~
.. code-block:: json

    {"email": "user@uw.edu", "password": "supersecret"}


POST Success Response
~~~~~~~~~~~~~~~~~~~~~~

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



/v1.0/nslc/	rest_framework.routers.APIRootView	nslc:api-root
/v1.0/nslc/\.<format>/	rest_framework.routers.APIRootView	nslc:api-root
/v1.0/nslc/channels/	nslc.views.ChannelViewSet	nslc:channel-list
/v1.0/nslc/channels/<pk>/	nslc.views.ChannelViewSet	nslc:channel-detail
/v1.0/nslc/channels/<pk>\.<format>/	nslc.views.ChannelViewSet	nslc:channel-detail
/v1.0/nslc/channels\.<format>/	nslc.views.ChannelViewSet	nslc:channel-list
/v1.0/nslc/groups/	nslc.views.GroupViewSet	nslc:group-list
/v1.0/nslc/groups/<pk>/	nslc.views.GroupViewSet	nslc:group-detail
/v1.0/nslc/groups/<pk>\.<format>/	nslc.views.GroupViewSet	nslc:group-detail
/v1.0/nslc/groups\.<format>/	nslc.views.GroupViewSet	nslc:group-list
/v1.0/nslc/networks/	nslc.views.NetworkViewSet	nslc:network-list
/v1.0/nslc/networks/<pk>/	nslc.views.NetworkViewSet	nslc:network-detail
/v1.0/nslc/networks/<pk>\.<format>/	nslc.views.NetworkViewSet	nslc:network-detail
/v1.0/nslc/networks\.<format>/	nslc.views.NetworkViewSet	nslc:network-list
