# Generated by Django 4.2.7 on 2023-11-08 10:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('business', '0003_alter_customer_phone_number'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='taxe',
            field=models.FloatField(choices=[(0.55, '50%'), (0.1, '10%'), (0.2, '20%')], default=0.2),
        ),
    ]
