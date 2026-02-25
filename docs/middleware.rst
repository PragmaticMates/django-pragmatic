Middleware
==========

MaintenanceModeMiddleware
--------------------------

``pragmatic.middleware.MaintenanceModeMiddleware``

Serves a ``503 Service Unavailable`` response for all requests when
``MAINTENANCE_MODE = True``, rendered from ``maintenance_mode.html``.

Setup
~~~~~

1. Add to ``MIDDLEWARE`` (position near the top so other middleware is bypassed):

   .. code-block:: python

       MIDDLEWARE = [
           'pragmatic.middleware.MaintenanceModeMiddleware',
           ...
       ]

2. Create ``templates/maintenance_mode.html`` in your project:

   .. code-block:: html

       <!DOCTYPE html>
       <html>
       <body>
           <h1>Down for maintenance</h1>
           <p>We'll be back shortly.</p>
       </body>
       </html>

   A default template is included at
   ``pragmatic/templates/maintenance_mode.html``.

3. Toggle maintenance mode in settings (or dynamically via environment variable /
   Django management command):

   .. code-block:: python

       MAINTENANCE_MODE = True

Bypassing for specific users
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

List user primary keys that should see the real site even during maintenance:

.. code-block:: python

    MAINTENANCE_MODE_BYPASS_USERS = [1]  # superuser id

Authenticated users whose ``pk`` is in this list bypass the maintenance screen.
