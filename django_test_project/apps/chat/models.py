from django.db import models
from django.contrib.auth import get_user_model


User = get_user_model()


class AbstractMessage(models.Model):
    user = models.ForeignKey(
        to=User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='%(class)s_messages',
    )
    chat = models.ForeignKey(
        to='chat.Chat',
        on_delete=models.CASCADE,
        related_name='%(class)s_messages',
    )
    message = models.TextField()

    class Meta:
        abstract = True


class Chat(models.Model):
    name = models.CharField(
        max_length=256,
    )


class Vote(models.Model):
    message = models.ForeignKey(
        to='chat.Message',
        on_delete=models.CASCADE,
        related_name='votes',
    )
    user = models.ForeignKey(
        to=User,
        on_delete=models.CASCADE,
        related_name='votes',
    )


class Message(AbstractMessage):
    pass


class Reply(AbstractMessage):
    parent_message = models.ForeignKey(
        to='chat.Message',
        on_delete=models.CASCADE,
        related_name='child_messages',
    )
