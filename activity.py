# -*- coding: utf-8 -*-
#Copyright (c) 2013,14 Walter Bender

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# You should have received a copy of the GNU General Public License
# along with this library; if not, write to the Free Software
# Foundation, 51 Franklin Street, Suite 500 Boston, MA 02110-1335 USA

from gi.repository import Gtk
import dbus
import os
from shutil import copy
import json
from gettext import gettext as _

from sugar3.activity import activity
from sugar3.graphics.toolbarbox import ToolbarBox
from sugar3.activity.widgets import ActivityToolbarButton
from sugar3.graphics.toolbarbox import ToolbarButton
from sugar3.activity.widgets import StopButton
from sugar3.graphics import style

from jarabe.view.viewhelp import ViewHelp

from toolbar_utils import separator_factory, label_factory, button_factory
from taskmaster import TaskMaster
from tasks import FONT_SIZES
from checkprogress import CheckProgress

import logging
_logger = logging.getLogger('training-activity')


class TrainingActivity(activity.Activity):
    ''' A series of training exercises '''

    def __init__(self, handle):
        ''' Initialize the toolbars and the game board '''
        try:
            super(TrainingActivity, self).__init__(handle)
        except dbus.exceptions.DBusException, e:
            _logger.error(str(e))

        self.connect('realize', self.__realize_cb)

        self.font_size = 5
        self.zoom_level = 0.833
        self.check_progress = None

        if hasattr(self, 'metadata') and 'font_size' in self.metadata:
            self.font_size = int(self.metadata['font_size'])

        self._setup_toolbars()

        self.modify_bg(Gtk.StateType.NORMAL,
                       style.COLOR_WHITE.get_gdk_color())

        self._task_master = TaskMaster(self)

        center_in_panel = Gtk.Alignment.new(0.5, 0, 0, 0)
        center_in_panel.add(self._task_master)
        self._task_master.show()
        self.set_canvas(center_in_panel)
        center_in_panel.show()

        self.completed = False
        self._task_master.task_master()

    def write_file(self, file_path):
        self._task_master.write_task_data('current_task',
                                        self._task_master.current_task)
        self.metadata['font_size'] = str(self.font_size)

    def _setup_toolbars(self):
        ''' Setup the toolbars. '''
        self.max_participants = 1  # No sharing

        toolbox = ToolbarBox()

        activity_button = ActivityToolbarButton(self)
        toolbox.toolbar.insert(activity_button, 0)
        activity_button.show()

        self.set_toolbar_box(toolbox)
        toolbox.show()
        self.toolbar = toolbox.toolbar

        view_toolbar = Gtk.Toolbar()
        view_toolbar_button = ToolbarButton(
            page=view_toolbar,
            icon_name='toolbar-view')
        toolbox.toolbar.insert(view_toolbar_button, 1)
        view_toolbar.show()
        view_toolbar_button.show()

        button_factory('view-fullscreen', view_toolbar,
                       self._fullscreen_cb, tooltip=_('Fullscreen'),
                       accelerator='<Alt>Return')

        self._zoom_in = button_factory('zoom-in',  # 'resize+',
                                       view_toolbar,
                                       self._zoom_in_cb,
                                       tooltip=_('Increase font size'))

        self._zoom_out = button_factory('zoom-out',  # 'resize-',
                                        view_toolbar,
                                        self._zoom_out_cb,
                                        tooltip=_('Decrease font size'))
        self._set_zoom_buttons_sensitivity()

        self.help_button = button_factory('toolbar-help',
                                          toolbox.toolbar,
                                          self._help_cb, tooltip=_('help'),
                                          accelerator=_('<Ctrl>H'))
        self.help_button.set_sensitive(False)

        progress = button_factory('check-progress',
                                  toolbox.toolbar,
                                  self._check_progress_cb,
                                  tooltip=_('Check progress'))

        self.back = button_factory('go-previous-paired',
                                   toolbox.toolbar,
                                   self._go_back_cb,
                                   tooltip=_('Previous section'))
        self.back.props.sensitive = False

        self.forward = button_factory('go-next-paired',
                                   toolbox.toolbar,
                                   self._go_forward_cb,
                                   tooltip=_('Next section'))
        self.forward.props.sensitive = False

        self.progress_label = label_factory(toolbox.toolbar, '', width=300)
        self.progress_label.set_use_markup(True)

        separator_factory(toolbox.toolbar, True, False)
        stop_button = StopButton(self)
        stop_button.props.accelerator = '<Ctrl>q'
        toolbox.toolbar.insert(stop_button, -1)
        stop_button.show()

    def __realize_cb(self, window):
        self.window_xid = window.get_window().get_xid()

    def _fullscreen_cb(self, button):
        ''' Hide the Sugar toolbars. '''
        self.fullscreen()

    def _set_zoom_buttons_sensitivity(self):
        if self.font_size < len(FONT_SIZES) - 1:
            self._zoom_in.set_sensitive(True)
        else:
            self._zoom_in.set_sensitive(False)
        if self.font_size > 0:
            self._zoom_out.set_sensitive(True)
        else:
            self._zoom_out.set_sensitive(False)

    def _zoom_in_cb(self, button):
        if self.font_size < len(FONT_SIZES) - 1:
            self.font_size += 1
            self.zoom_level *= 1.1
        self._set_zoom_buttons_sensitivity()
        self._task_master.reload_graphics()

    def _zoom_out_cb(self, button):
        if self.font_size > 0:
            self.font_size -= 1
            self.zoom_level /= 1.1
        self._set_zoom_buttons_sensitivity()
        self._task_master.reload_graphics()

    def _check_progress_cb(self, button):
        self.check_progress = CheckProgress(self._task_master)
        self._task_master.load_progress_summary(self.check_progress)

    def _go_back_cb(self, button):
        section, task = self._task_master.get_section_index()
        if section > 0:
            section -= 1
        _logger.debug('go back %d:%d' % (section, task))
        uid = self._task_master.section_and_task_to_uid(section)
        _logger.debug('new uid %s' % (uid))
        self._task_master.current_task = \
            self._task_master.uid_to_task_number(uid)
        self._task_master.task_master()

    def _go_forward_cb(self, button):
        section, task = self._task_master.get_section_index()
        if section < self._task_master.get_number_of_sections() - 1:
            section += 1
        _logger.debug('go forward %d:%d' % (section, task))
        uid = self._task_master.section_and_task_to_uid(section)
        _logger.debug('new uid %s' % (uid))
        self._task_master.current_task = \
            self._task_master.uid_to_task_number(uid)
        self._task_master.task_master()

    def _help_cb(self, button):
        title, help_file = self._task_master.get_help_info()
        _logger.debug('%s: %s' % (title, help_file))
        if not hasattr(self, 'window_xid'):
            self.window_xid = self.get_window().get_xid()
        if title is not None and help_file is not None:
            self.viewhelp = ViewHelp(title, help_file, self.window_xid)
            self.viewhelp.show()

    def add_badge(self, msg, icon="training-trophy", name="One Academy"):
        badge = {
            'icon': icon,
            'from': name,
            'message': msg
        }
        icon_path = os.path.join(activity.get_bundle_path(),
                                 'icons',
                                 (icon + '.svg'))
        sugar_icons = os.path.join(os.path.expanduser('~'), '.icons')
        copy(icon_path, sugar_icons)

        if 'comments' in self.metadata:
            comments = json.loads(self.metadata['comments'])
            comments.append(badge)
            self.metadata['comments'] = json.dumps(comments)
        else:
            self.metadata['comments'] = json.dumps([badge])
