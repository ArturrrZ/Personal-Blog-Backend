# Generated by Django 5.1.4 on 2025-02-12 17:37

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0013_subscriptionplan_stripe_subscription_id_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='subscriptionplan',
            name='stripe_subscription_id',
        ),
    ]
