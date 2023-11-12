from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import gettext_lazy as _


class DeletedObject(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField(_('object ID'))
    object_str = models.CharField(_('object representation'), max_length=300)
    user = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL,
        blank=True, null=True, default=None)
    datetime = models.DateTimeField(_('datetime'), auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = _('deleted object')
        verbose_name_plural = _('deleted objects')
        ordering = ('datetime',)
        get_latest_by = 'datetime'
        default_permissions = getattr(settings, 'DEFAULT_PERMISSIONS', ('add', 'change', 'delete', 'view'))

    def __str__(self):
        return self.object_str
