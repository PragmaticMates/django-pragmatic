from helpers import get_subclasses


def receiver_subclasses(signal, sender, dispatch_uid_prefix, **kwargs):
    """
    A decorator for connecting receivers and all receiver's subclasses to signals. Used by passing in the
    signal and keyword arguments to connect::

        @receiver_subclasses(post_save, MyModel, 'mymodel_post_save')
        def signal_receiver(sender, **kwargs):
            ...

    Thanks to: http://codeblogging.net/blogs/1/14/
    """
    def _decorator(func):
        all_senders = get_subclasses(sender)
        #logging.info(all_senders)
        for snd in all_senders:
            signal.connect(func, sender=snd, dispatch_uid=dispatch_uid_prefix+'_'+snd.__name__, **kwargs)
        return func
    return _decorator
