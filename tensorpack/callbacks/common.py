#!/usr/bin/env python2
# -*- coding: UTF-8 -*-
# File: common.py
# Author: Yuxin Wu <ppwwyyxx@gmail.com>

import tensorflow as tf
import os
import re

from .base import Callback, PeriodicCallback
from ..utils import *

__all__ = ['PeriodicSaver', 'SummaryWriter']

class PeriodicSaver(PeriodicCallback):
    def __init__(self, period=1, keep_recent=10, keep_freq=0.5):
        super(PeriodicSaver, self).__init__(period)
        self.path = os.path.join(logger.LOG_DIR, 'model')
        self.keep_recent = keep_recent
        self.keep_freq = keep_freq

    def _before_train(self):
        self.saver = tf.train.Saver(
            max_to_keep=self.keep_recent,
            keep_checkpoint_every_n_hours=self.keep_freq)

    def _trigger_periodic(self):
        self.saver.save(
            tf.get_default_session(),
            self.path,
            global_step=self.global_step)

class SummaryWriter(Callback):
    def __init__(self, print_tag=None):
        """ if None, print all scalar summary"""
        self.log_dir = logger.LOG_DIR
        self.print_tag = print_tag

    def _before_train(self):
        self.writer = tf.train.SummaryWriter(
            self.log_dir, graph_def=self.sess.graph_def)
        tf.add_to_collection(SUMMARY_WRITER_COLLECTION_KEY, self.writer)
        self.summary_op = tf.merge_all_summaries()
        self.epoch_num = 0

    def _trigger_epoch(self):
        self.epoch_num += 1
        # check if there is any summary to write
        if self.summary_op is None:
            return
        summary_str = self.summary_op.eval()
        summary = tf.Summary.FromString(summary_str)
        printed_tag = set()
        for val in summary.value:
            if val.WhichOneof('value') == 'simple_value':
                val.tag = re.sub('tower[0-9]*/', '', val.tag)
                if self.print_tag is None or val.tag in self.print_tag:
                    logger.info('{}: {:.4f}'.format(val.tag, val.simple_value))
                    printed_tag.add(val.tag)
        self.writer.add_summary(summary, get_global_step())
        if self.print_tag is not None and self.epoch_num == 1:
            if len(printed_tag) != len(self.print_tag):
                logger.warn("Tags to print not found in Summary Writer: {}".format(
                    ", ".join([k for k in self.print_tag if k not in printed_tag])))

    def _after_train(self):
        self.writer.close()

