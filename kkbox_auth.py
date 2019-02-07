from __future__ import unicode_literals

from flask_dance.consumer import OAuth2ConsumerBlueprint
from functools import partial
from flask.globals import LocalProxy, _lookup_app_object
try:
    from flask import _app_ctx_stack as stack
except ImportError:
    from flask import _request_ctx_stack as stack


def make_kkbox_blueprint(client_id=None,
                         client_secret=None,
                         authorization_url_params=None,
                         scope=None,
                         redirect_url=None,
                         redirect_to=None,
                         login_url=None,
                         authorized_url=None,
                         rerequest_declined_permissions=False,
                         session_class=None,
                         backend=None):
    """
    Make a blueprint for authenticating with KKBOX using OAuth 2. This requires
    a client ID and client secret from KKBOX. You should either pass them to
    this constructor, or make sure that your Flask application config defines
    them, using the variables KKBOX_OAUTH_CLIENT_ID and KKBOX_OAUTH_CLIENT_SECRET.

    Args:
        client_id (str): The client ID for your application on KKBOX.
        client_secret (str): The client secret for your application on KKBOX
        scope (str, optional): comma-separated list of scopes for the OAuth token
        redirect_url (str): the URL to redirect to after the authentication
            dance is complete
        redirect_to (str): if ``redirect_url`` is not defined, the name of the
            view to redirect to after the authentication dance is complete.
            The actual URL will be determined by :func:`flask.url_for`
        login_url (str, optional): the URL path for the ``login`` view.
            Defaults to ``/kkbox``
        authorized_url (str, optional): the URL path for the ``authorized`` view.
            Defaults to ``/kkbox/authorized``.
        rerequest_declined_permissions (bool, optional): should the blueprint ask again for declined permissions.
            Defaults to ``False``
        session_class (class, optional): The class to use for creating a
            Requests session. Defaults to
            :class:`~flask_dance.consumer.requests.OAuth2Session`.
        backend: A storage backend class, or an instance of a storage
                backend class, to use for this blueprint. Defaults to
                :class:`~flask_dance.consumer.backend.session.SessionBackend`.

    :rtype: :class:`~flask_dance.consumer.OAuth2ConsumerBlueprint`
    :returns: A :ref:`blueprint <flask:blueprints>` to attach to your Flask app.
    """
    kkbox_bp = OAuth2ConsumerBlueprint(
        "kkbox",
        __name__,
        client_id=client_id,
        client_secret=client_secret,
        scope=scope,
        base_url="https://account.kkbox.com/oauth2/",
        authorization_url="https://account.kkbox.com/oauth2/authorize/",
        authorization_url_params=authorization_url_params,
        token_url="https://account.kkbox.com/oauth2/token/",
        redirect_url=redirect_url,
        redirect_to=redirect_to,
        login_url=login_url,
        authorized_url=authorized_url,
        session_class=session_class,
        backend=backend,
    )
    kkbox_bp.from_config["client_id"] = "KKBOX_OAUTH_CLIENT_ID"
    kkbox_bp.from_config["client_secret"] = "KKBOX_OAUTH_CLIENT_SECRET"

    @kkbox_bp.before_app_request
    def set_applocal_session():
        ctx = stack.top
        ctx.facebook_oauth = kkbox_bp.session

    return kkbox_bp