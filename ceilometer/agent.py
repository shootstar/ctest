# -*- encoding: utf-8 -*-
#
# Copyright © 2013 Julien Danjou
#
# Author: Julien Danjou <julien@danjou.info>
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import abc
import itertools

from oslo.config import cfg
from stevedore import dispatch

from ceilometer.logger import logger
from ceilometer.openstack.common import context
from ceilometer.openstack.common import log
from ceilometer import pipeline

LOG = log.getLogger(__name__)


class PollingTask(object):
    """Polling task for polling counters and inject into pipeline
    A polling task can be invoked periodically or only once"""

    def __init__(self, agent_manager):
        self.manager = agent_manager
        self.pollsters = set()
        self.publish_context = pipeline.PublishContext(
            agent_manager.context,
            cfg.CONF.counter_source)

    def add(self, pollster, pipelines):
        self.publish_context.add_pipelines(pipelines)
        self.pollsters.update([pollster])

    @abc.abstractmethod
    def poll_and_publish(self):
        """Polling counter and publish into pipeline."""


class AgentManager(object):

    def __init__(self, extension_manager):
        logger.debug("AGENT MANAGER")
        publisher_manager = dispatch.NameDispatchExtensionManager(
            namespace=pipeline.PUBLISHER_NAMESPACE,
            check_func=lambda x: True,
            invoke_on_load=True,
        )

        self.pipeline_manager = pipeline.setup_pipeline(publisher_manager)

        self.pollster_manager = extension_manager

        self.context = context.RequestContext('admin', 'admin', is_admin=True)
        logger.debug("pipeline manager:{}".format(self.pipeline_manager))
        logger.debug("pollster manager:{}".format(self.pollster_manager))
  
    @abc.abstractmethod
    def create_polling_task(self):
        """Create an empty polling task."""

    def setup_polling_tasks(self):
        polling_tasks = {}
        logger.debug("setup polling tasks")       
        for pipeline, pollster in itertools.product(
                self.pipeline_manager.pipelines,
                self.pollster_manager.extensions):
            logger.debug("pipeline:{},pollster:{}".format(pipeline,pollster))
            for counter in pollster.obj.get_counter_names():
                logger.debug("counter:{}".format(counter))
                if pipeline.support_counter(counter):
                    logger.debug("pipeline support counter:{}".format(counter))
                    polling_task = polling_tasks.get(pipeline.interval, None)
                    if not polling_task:
                        polling_task = self.create_polling_task()
                        polling_tasks[pipeline.interval] = polling_task
                    polling_task.add(pollster, [pipeline])
                    break
        logger.debug("POLLINGTASK:{}".format([p.name for p in polling_task.pollsters]))
        return polling_tasks

    def initialize_service_hook(self, service):
        logger.debug("service:{}".format(service))
        self.service = service
        for interval, task in self.setup_polling_tasks().iteritems():
            logger.debug("intervak:{} task:{}".format(interval,task))
            self.service.tg.add_timer(interval,
                                      self.interval_task,
                                      task=task)

    def interval_task(self, task):
        task.poll_and_publish()
