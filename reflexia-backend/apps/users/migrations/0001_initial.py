
import django.db.models.deletion
import django.utils.timezone
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('first_name', models.CharField(max_length=100)),
                ('last_name', models.CharField(max_length=150)),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('registration_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('two_factor_enabled', models.BooleanField(default=False)),
                ('is_active', models.BooleanField(default=True)),
                ('is_staff', models.BooleanField(default=False)),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
            ],
            options={
                'verbose_name': 'user',
                'verbose_name_plural': 'users',
            },
        ),
        migrations.CreateModel(
            name='Patient',
            fields=[
                ('user_ptr', models.OneToOneField(db_column='id', on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, related_name='patient', serialize=False, to=settings.AUTH_USER_MODEL)),
                ('birth_date', models.DateField()),
                ('consent_accepted', models.BooleanField(default=False)),
                ('consent_date', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'verbose_name': 'patient',
                'verbose_name_plural': 'patients',
            },
            bases=('users.user',),
        ),
        migrations.CreateModel(
            name='Therapist',
            fields=[
                ('user_ptr', models.OneToOneField(db_column='id', on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, related_name='therapist', serialize=False, to=settings.AUTH_USER_MODEL)),
                ('license_number', models.CharField(max_length=100)),
                ('specialty', models.CharField(max_length=150)),
            ],
            options={
                'verbose_name': 'therapist',
                'verbose_name_plural': 'therapists',
            },
            bases=('users.user',),
        ),
    ]
