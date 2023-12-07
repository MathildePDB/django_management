# Generated by Django 4.2.7 on 2023-11-08 10:48

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('business', '0006_alter_product_taxe'),
    ]

    operations = [
        migrations.CreateModel(
            name='OrderDetail',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.PositiveIntegerField()),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='business.order')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='business.product')),
            ],
        ),
    ]