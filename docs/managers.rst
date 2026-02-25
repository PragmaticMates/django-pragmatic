Managers
========

EmailManager
------------

``pragmatic.managers.EmailManager``

Sends HTML and/or plain-text emails rendered from Django templates, with
optional background dispatch via RQ.

Usage
~~~~~

.. code-block:: python

    from pragmatic.managers import EmailManager

    EmailManager.send_mail(
        to=user,                          # User instance or email string, or list of either
        template_prefix='emails/welcome', # loads welcome.txt and/or welcome.html
        subject='Welcome to our service',
        data={'activation_link': url},    # extra template context
        request=request,                  # optional; adds site to context
        attachments=[                     # optional file attachments
            {
                'filename': 'invoice.pdf',
                'content': pdf_bytes,
                'content_type': 'application/pdf',
            }
        ],
        reply_to=support_user,            # optional reply-to address
    )

Template discovery
~~~~~~~~~~~~~~~~~~

``EmailManager.send_mail`` looks for:

- ``{template_prefix}.txt`` — plain-text body (optional)
- ``{template_prefix}.html`` — HTML alternative (optional)

At least one of the two should exist. The rendered template receives:

.. list-table::
   :widths: 25 75
   :header-rows: 1

   * - Variable
     - Value
   * - ``subject``
     - The subject string passed to ``send_mail``
   * - ``request``
     - The request object (or ``None``)
   * - ``site``
     - Result of ``get_current_site(request)``
   * - ``settings``
     - The Django settings module
   * - ``recipient``
     - The ``to`` object (only when ``to`` is not a list)
   * - *(custom)*
     - Any keys from the ``data`` argument

Background sending
~~~~~~~~~~~~~~~~~~

When ``MAILS_QUEUE`` is set in settings, emails are enqueued via
``send_mail_in_background.delay(email)`` instead of being sent
synchronously. Requires ``django-rq`` to be installed and configured.

.. code-block:: python

    # settings.py
    MAILS_QUEUE = 'default'   # name of an RQ queue

When ``MAILS_QUEUE`` is ``None`` (the default), ``email.send()`` is called
immediately and its return value is returned by ``send_mail``.

Helper methods
~~~~~~~~~~~~~~

``EmailManager.get_recipient(to)``
    Returns ``to`` if it is already a string, otherwise ``to.email``.

``EmailManager.get_recipients(to)``
    Returns a list of email address strings, accepting a single object, a
    string, or a list of either.
