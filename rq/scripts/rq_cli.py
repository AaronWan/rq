#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
rq command line tool
"""
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import click
import redis
from rq import get_failed_queue, Queue
from rq.exceptions import InvalidJobOperationError

from .rqinfo import info


@click.group()
@click.option('--url', '-u', envvar='URL',
        help='URL describing Redis connection details.')
@click.pass_context
def main(ctx, url):
    """Entrance of RQ CLI"""
    if url is None:
        url = "redis://localhost:6379/0"
    redis_conn = redis.from_url(url)

    ctx.obj = {}
    ctx.obj['connection'] = redis_conn


@main.command()
@click.option('--yes', '-y', is_flag=True,
        help='Empty failed queue by default')
@click.argument('queues', nargs=-1)
@click.pass_context
def empty(ctx, yes, queues):
    """[QUEUES]: queues to empty

    \b
    $ rq empty
    Do you want to empty failed queue? [y/N]: y
    2 jobs removed from failed queue
    \b
    $ rq empty -y
    2 jobs removed from failed queue
    \b
    $ rq empty default high
    10 jobs removed from default queue
    2 jobs removed from high queue
    """
    conn = ctx.obj['connection']
    queues = [Queue(queue, connection=conn) for queue in queues]
    if not queues:
        if yes or click.confirm('Do you want to empty failed queue?',
                abort=True):
            queues = (get_failed_queue(connection=conn),)
    for queue in queues:
        num_jobs = queue.empty()
        click.echo('{0} jobs removed from {1} queue'.format(num_jobs, queue.name))


@main.command()
@click.pass_context
def requeue(ctx):
    """Requeue all failed jobs in failed queue"""
    conn = ctx.obj['connection']
    failed_queue = get_failed_queue(connection=conn)
    job_ids = failed_queue.job_ids
    click.echo('Requeue failed jobs: {0}'.format(len(job_ids)))
    requeue_failed_num = 0
    with click.progressbar(job_ids) as job_bar:
        for job_id in job_bar:
            try:
                failed_queue.requeue(job_id)
            except InvalidJobOperationError:
                requeue_failed_num += 1

    click.secho('Requeue failed: {0}'.format(
        requeue_failed_num), fg='red')


main.add_command(info)
