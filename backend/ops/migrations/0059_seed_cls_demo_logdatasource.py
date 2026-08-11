from django.db import migrations


def seed_cls_demo_log_datasource(apps, schema_editor):
    LogDataSource = apps.get_model('ops', 'LogDataSource')

    LogDataSource.objects.get_or_create(
        name='CLS Demo',
        defaults={
            'provider': 'cls',
            'description': 'Demo datasource. Replace endpoint, region, topic_id, and SecretId/SecretKey before use.',
            'config': {
                'endpoint': 'cls.tencentcloudapi.com',
                'region': 'ap-guangzhou',
                'topic_id': 'demo-topic-001',
                'topic': 'demo-cls-topic',
                'secret_id': 'demo-secret-id',
                'secret_key': 'demo-secret-key',
                'demo_mode': True,
                'demo_topics': ['demo-cls-topic', 'demo-audit-topic'],
            },
            'is_enabled': True,
            'is_default': False,
        },
    )


def noop(apps, schema_editor):
    return None


class Migration(migrations.Migration):
    dependencies = [
        ('ops', '0058_taskresourcegroup_event_environment'),
    ]

    operations = [
        migrations.RunPython(seed_cls_demo_log_datasource, noop),
    ]
