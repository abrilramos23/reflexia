from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_remove_patient_therapist_therapistpatient'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProfessionalDirectoryEntry',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('license_number', models.CharField(max_length=100, unique=True)),
                ('complete_name', models.CharField(max_length=255)),
            ],
            options={
                'verbose_name': 'professional directory entry',
                'verbose_name_plural': 'professional directory entries',
            },
        ),
        migrations.AlterField(
            model_name='therapist',
            name='license_number',
            field=models.CharField(max_length=100, unique=True),
        ),
    ]
