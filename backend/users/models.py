from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """User class."""

    username = models.CharField(
        max_length=150,
        unique=True,
        help_text=('Required fields. Max 150 symbols.'
                   'Letters, figures and symbols @/./+/-/_. only'
                   ),
        error_messages={
            'unique': ('This username already exists')
        },
        verbose_name='Login',
    )
    email = models.EmailField(
        max_length=128,
        unique=True,
        blank=False,
        null=False,
        verbose_name='E-mail',
    )
    first_name = models.CharField(
        max_length=128,
        verbose_name='First Name',
    )
    last_name = models.CharField(
        max_length=128,
        verbose_name='Last Name'
    )

    def __str__(self) -> str:
        return self.username


class Follow(models.Model):
    """Follow class."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscribes',
        verbose_name='Subscribes',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscribers',
        verbose_name='Author',
    )

    class Meta:
        verbose_name = 'Subscription'
        verbose_name_plural = 'Subscriptions'
        constraints = (
            models.CheckConstraint(
                check=~models.Q(user=models.F('author')),
                name='no_self_subscribe'
            ),
            models.UniqueConstraint(
                fields=('user', 'author'),
                name='unique_subscription'
            )
        )

    def __str__(self):
        return f'{self.user}: {self.author}'
