# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# Generated by Django 1.11.16 on 2018-12-21 10:56
# pylint: disable=invalid-name,too-few-public-methods
"""Migration for the update of the DbLog table. Addition of uuids"""

from __future__ import division
from __future__ import unicode_literals
from __future__ import absolute_import

from __future__ import print_function
import sys
from six.moves import zip
import click

# Remove when https://github.com/PyCQA/pylint/issues/1931 is fixed
# pylint: disable=no-name-in-module,import-error
from django.db import migrations, models
from aiida.backends.djsite.db.migrations import upgrade_schema_version
from aiida.common.utils import get_new_uuid
from aiida.manage import configuration

REVISION = '1.0.24'
DOWN_REVISION = '1.0.23'

# The values that will be exported for the log records that will be deleted
values_to_export = ['id', 'time', 'loggername', 'levelname', 'objpk', 'objname', 'message', 'metadata']

node_prefix = 'node.'
leg_workflow_prefix = 'aiida.workflows.user.'


def get_legacy_workflow_log_number(schema_editor):
    """ Get the number of the log records that correspond to legacy workflows """
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("""
            SELECT COUNT(*) FROM db_dblog
            WHERE
                (db_dblog.objname LIKE 'aiida.workflows.user.%')
            """)
        return cursor.fetchall()[0][0]


def get_unknown_entity_log_number(schema_editor):
    """ Get the number of the log records that correspond to unknown entities """
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("""
            SELECT COUNT(*) FROM db_dblog
            WHERE
                (db_dblog.objname NOT LIKE 'node.%') AND
                (db_dblog.objname NOT LIKE 'aiida.workflows.user.%')
            """)
        return cursor.fetchall()[0][0]


def get_logs_with_no_nodes_number(schema_editor):
    """ Get the number of the log records that don't correspond to a node """
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("""
            SELECT COUNT(*) FROM db_dblog
            WHERE
                (db_dblog.objname LIKE 'node.%') AND NOT EXISTS
                (SELECT 1 FROM db_dbnode WHERE db_dbnode.id = db_dblog.objpk LIMIT 1)
            """)
        return cursor.fetchall()[0][0]


def get_serialized_legacy_workflow_logs(schema_editor):
    """ Get the serialized log records that correspond to legacy workflows """
    from aiida.backends.sqlalchemy.utils import dumps_json
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(("""
            SELECT db_dblog.id, db_dblog.time, db_dblog.loggername, db_dblog.levelname, db_dblog.objpk, db_dblog.objname,
            db_dblog.message, db_dblog.metadata FROM db_dblog
            WHERE
                (db_dblog.objname LIKE 'aiida.workflows.user.%')
            """))
        keys = ['id', 'time', 'loggername', 'levelname', 'objpk', 'objname', 'message', 'metadata']
        res = list()
        for row in cursor.fetchall():
            res.append(dict(list(zip(keys, row))))
        return dumps_json(res)


def get_serialized_unknown_entity_logs(schema_editor):
    """ Get the serialized log records that correspond to unknown entities """
    from aiida.backends.sqlalchemy.utils import dumps_json
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(("""
            SELECT db_dblog.id, db_dblog.time, db_dblog.loggername, db_dblog.levelname, db_dblog.objpk, db_dblog.objname,
            db_dblog.message, db_dblog.metadata FROM db_dblog
            WHERE
                (db_dblog.objname NOT LIKE 'node.%') AND
                (db_dblog.objname NOT LIKE 'aiida.workflows.user.%')
            """))
        keys = ['id', 'time', 'loggername', 'levelname', 'objpk', 'objname', 'message', 'metadata']
        res = list()
        for row in cursor.fetchall():
            res.append(dict(list(zip(keys, row))))
        return dumps_json(res)


def get_serialized_logs_with_no_nodes(schema_editor):
    """ Get the serialized log records that don't correspond to a node """
    from aiida.backends.sqlalchemy.utils import dumps_json
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(("""
            SELECT db_dblog.id, db_dblog.time, db_dblog.loggername, db_dblog.levelname, db_dblog.objpk, db_dblog.objname,
            db_dblog.message, db_dblog.metadata FROM db_dblog
            WHERE
                (db_dblog.objname LIKE 'node.%') AND NOT EXISTS
                (SELECT 1 FROM db_dbnode WHERE db_dbnode.id = db_dblog.objpk LIMIT 1)
            """))
        keys = ['id', 'time', 'loggername', 'levelname', 'objpk', 'objname', 'message', 'metadata']
        res = list()
        for row in cursor.fetchall():
            res.append(dict(list(zip(keys, row))))
        return dumps_json(res)


def set_new_uuid(apps, _):
    """
    Set new UUIDs for all logs
    """
    DbLog = apps.get_model('db', 'DbLog')
    for log in DbLog.objects.all():
        log.uuid = get_new_uuid()
        log.save(update_fields=['uuid'])


def export_and_clean_workflow_logs(apps, schema_editor):
    """
    Export the logs records that correspond to legacy workflows and to unknown entities.
    """
    from tempfile import NamedTemporaryFile

    DbLog = apps.get_model('db', 'DbLog')

    lwf_number = get_legacy_workflow_log_number(schema_editor)
    other_number = get_unknown_entity_log_number(schema_editor)
    log_no_node_number = get_logs_with_no_nodes_number(schema_editor)

    # If there are no legacy workflow log records or log records of an unknown entity
    if lwf_number == 0 and other_number == 0 and log_no_node_number == 0:
        return

    if not configuration.PROFILE.is_test_profile:
        click.echo('We found {} log records that correspond to legacy workflows and {} log records to correspond '
                   'to an unknown entity.'.format(lwf_number, other_number))
        click.echo(
            'These records will be removed from the database and exported to JSON files to the current directory).')
        proceed = click.confirm('Would you like to proceed?', default=True)
        if not proceed:
            sys.exit(1)

    delete_on_close = configuration.PROFILE.is_test_profile

    # Exporting the legacy workflow log records
    if lwf_number != 0:
        # Get the records and write them to file
        with NamedTemporaryFile(
                prefix='legagy_wf_logs-', suffix='.log', dir='.', delete=delete_on_close, mode='w+') as handle:
            filename = handle.name
            handle.write(get_serialized_legacy_workflow_logs(schema_editor))

        # If delete_on_close is False, we are running for the user and add additional message of file location
        if not delete_on_close:
            click.echo('Exported legacy workflow logs to {}'.format(filename))

        # Now delete the records
        DbLog.objects.filter(objname__startswith=leg_workflow_prefix).delete()
        with schema_editor.connection.cursor() as cursor:
            cursor.execute(("""
                DELETE FROM db_dblog
                WHERE
                    (db_dblog.objname LIKE 'aiida.workflows.user.%')
                """))

    # Exporting unknown log records
    if other_number != 0:
        # Get the records and write them to file
        with NamedTemporaryFile(
                prefix='unknown_entity_logs-', suffix='.log', dir='.', delete=delete_on_close, mode='w+') as handle:
            filename = handle.name
            handle.write(get_serialized_unknown_entity_logs(schema_editor))

        # If delete_on_close is False, we are running for the user and add additional message of file location
        if not delete_on_close:
            click.echo('Exported unexpected entity logs to {}'.format(filename))

        # Now delete the records
        DbLog.objects.exclude(objname__startswith=node_prefix).exclude(objname__startswith=leg_workflow_prefix).delete()
        with schema_editor.connection.cursor() as cursor:
            cursor.execute(("""
                DELETE FROM db_dblog WHERE
                    (db_dblog.objname NOT LIKE 'node.%') AND
                    (db_dblog.objname NOT LIKE 'aiida.workflows.user.%')
                """))

    # Exporting log records that don't correspond to nodes
    if log_no_node_number != 0:
        # Get the records and write them to file
        with NamedTemporaryFile(
                prefix='no_node_entity_logs-', suffix='.log', dir='.', delete=delete_on_close, mode='w+') as handle:
            filename = handle.name
            handle.write(get_serialized_logs_with_no_nodes(schema_editor))

        # If delete_on_close is False, we are running for the user and add additional message of file location
        if not delete_on_close:
            click.echo('Exported entity logs that don\'t correspond to nodes to {}'.format(filename))

        # Now delete the records
        with schema_editor.connection.cursor() as cursor:
            cursor.execute(("""
                DELETE FROM db_dblog WHERE
                (db_dblog.objname LIKE 'node.%') AND NOT EXISTS
                (SELECT 1 FROM db_dbnode WHERE db_dbnode.id = db_dblog.objpk LIMIT 1)
                """))


def clean_dblog_metadata(apps, _):
    """
    Remove objpk and objname from the DbLog table metadata.
    """
    import json

    DbLog = apps.get_model('db', 'DbLog')
    for log in DbLog.objects.all():
        met = json.loads(log.metadata)
        if 'objpk' in met:
            del met['objpk']
        if 'objname' in met:
            del met['objname']
        log.metadata = json.dumps(met)
        log.save(update_fields=['metadata'])


def enrich_dblog_metadata(apps, _):
    """
    Add objpk and objname to the DbLog table metadata.
    """
    import json

    DbLog = apps.get_model('db', 'DbLog')
    for log in DbLog.objects.all():
        met = json.loads(log.metadata)
        if 'objpk' not in met:
            met['objpk'] = log.objpk
        if 'objname' not in met:
            met['objname'] = log.objname
        log.metadata = json.dumps(met)
        log.save(update_fields=['metadata'])


class Migration(migrations.Migration):
    """
    This migration updates the DbLog schema and adds UUID for correct export of the DbLog entries.
    More specifically, it adds UUIDS, it exports to files the not needed log entries (that correspond
    to legacy workflows and unknown entities), it creates a foreign key to the dbnode table, it
    transfers there the objpk data to the new dbnode column (just altering the objpk column and making
    it a foreign key when containing data, raised problems) and in the end objpk and objname columns
    are removed.
    """

    dependencies = [
        ('db', '0023_calc_job_option_attribute_keys'),
    ]

    operations = [
        # Export of the logs of the old workflows to a JSON file, there is no re-import
        # for the reverse migrations
        migrations.RunPython(export_and_clean_workflow_logs, reverse_code=migrations.RunPython.noop),

        # Removing objname and objpk from the metadata. The reverse migration adds the
        # objname and objpk to the metadata
        migrations.RunPython(clean_dblog_metadata, reverse_code=enrich_dblog_metadata),

        # The forward migration will not do anything for the objname, the reverse
        # migration will populate it with correct values
        migrations.RunSQL(
            '',
            reverse_sql='UPDATE db_dblog SET objname=db_dbnode.type '
            'FROM db_dbnode WHERE db_dbnode.id = db_dblog.objpk'),

        # Removal of the column objname, the reverse migration will add it
        migrations.RemoveField(model_name='dblog', name='objname'),

        # Creation of a new column called dbnode which is a foreign key to the dbnode table
        # The reverse migration will remove this column
        migrations.AddField(
            model_name='dblog',
            name='dbnode',
            field=models.ForeignKey(
                on_delete=models.deletion.CASCADE, related_name='dblogs', to='db.DbNode', blank=True, null=True),
        ),

        # Transfer of the data from the objpk to the node field
        # The reverse migration will do the inverse transfer
        migrations.RunSQL('UPDATE db_dblog SET dbnode_id=objpk', reverse_sql='UPDATE db_dblog SET objpk=dbnode_id'),

        # Now that all the data have been migrated, make the column not nullable and not blank.
        # A log record should always correspond to a node record
        migrations.AlterField(
            model_name='dblog',
            name='dbnode',
            field=models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='dblogs', to='db.DbNode'),
        ),

        # Since the new column is created correctly, drop the old objpk column
        # The reverse migration will add the field
        migrations.RemoveField(model_name='dblog', name='objpk'),

        # This is the correct pattern to generate unique fields, see
        # https://docs.djangoproject.com/en/1.11/howto/writing-migrations/#migrations-that-add-unique-fields
        # The reverse migration will remove it
        migrations.AddField(
            model_name='dblog',
            name='uuid',
            field=models.UUIDField(default=get_new_uuid, null=True),
        ),

        # Add unique UUIDs to the UUID field. There is no need for a reverse migration for a field
        # tha will be deleted
        migrations.RunPython(set_new_uuid, reverse_code=migrations.RunPython.noop),

        # Changing the column to unique
        migrations.AlterField(
            model_name='dblog',
            name='uuid',
            field=models.UUIDField(default=get_new_uuid, unique=True),
        ),
        upgrade_schema_version(REVISION, DOWN_REVISION)
    ]