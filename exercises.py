# -*- coding: utf-8 -*-
# Copyright (c) 2013 Walter Bender

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# You should have received a copy of the GNU General Public License
# along with this library; if not, write to the Free Software
# Foundation, 51 Franklin Street, Suite 500 Boston, MA 02110-1335 USA

import os
import json
import time
from gettext import gettext as _

from gi.repository import Gtk
from gi.repository import GObject
from gi.repository import WebKit

from sugar3 import profile
from sugar3 import env
from sugar3.graphics import style
from sugar3.graphics.toolbutton import ToolButton

import logging
_logger = logging.getLogger('training-activity-exercises')

ACCOUNT_NAME = 'mock'


def make_html_graphic(uri):
    web_view = WebKit.WebView()
    web_view.set_full_content_zoom(True)
    web_view.show()
    web_view.load_uri(uri)

    return web_view


def make_entry_graphic(task, dictionary):
    ''' dictionary is [{'title':, 'text':, 'caption': }, ]'''
    box = Gtk.VBox()
    for i in range(len(dictionary)):
        text = dictionary[i].get('text', '')
        title = dictionary[i].get('title', None)
        maxwidth = dictionary[i].get('max', 60)
        tooltip = dictionary[i].get('tooltip', None)
        caption = dictionary[i].get('caption', None)
        if title is not None:
            title_label= Gtk.Label(
                '<span foreground="%s" size="large"><b>%s</b></span>' %
                (style.COLOR_BLACK.get_html(), title))
            title_label.set_use_markup(True)
            title_label.set_line_wrap(True)
            title_label.set_property('xalign', 0.5)
            box.pack_start(title_label, True, True, 0)
            title_label.show()
        alignment_box = Gtk.Alignment.new(xalign=0.5, yalign=0.5,
                                          xscale=0, yscale=0)
        box.pack_start(alignment_box, True, False, 5)
        entry = Gtk.Entry()
        entry.set_text(text)
        if tooltip is not None and hasattr(entry, 'set_tooltip_text'):
            entry.set_tooltip_text(tooltip)
        entry.set_width_chars(maxwidth)
        toolitem = Gtk.ToolItem()
        toolitem.add(entry)
        entry.show()
        hbox = Gtk.HBox()
        hbox.pack_start(toolitem, False, False, 5)
        toolitem.show()
        def _button_cb(button):
            _logger.debug(entry.get_text())
            task.entries[i] = entry.get_text()
        button = ToolButton('dialog-ok')
        button.connect('clicked', _button_cb)
        button.show()
        hbox.pack_start(button, False, False, 5)
        alignment_box.add(hbox)
        hbox.show()
        alignment_box.show()
        if caption is not None:
            caption_label = Gtk.Label(
                '<span foreground="%s">%s</span>' %
                (style.COLOR_BUTTON_GREY.get_html(), caption))
            caption_label.set_use_markup(True)
            caption_label.set_line_wrap(True)
            caption_label.set_property('xalign', 0.5)
            box.pack_start(caption_label, True, True, 0)
            caption_label.show()
    return box


def make_image_graphic(dictionary):
    ''' dictionary is [{'title':, 'path':, 'caption': }, ]'''
    box = Gtk.VBox()
    for i in range(len(dictionary)):
        title = dictionary[i].get('title', None)
        path = dictionary[i].get('path', None)
        caption = dictionary[i].get('caption', None)
        if title is not None:
            title_label= Gtk.Label(
                '<span foreground="%s" size="large"><b>%s</b></span>' %
                (style.COLOR_BLACK.get_html(), title))
            title_label.set_use_markup(True)
            title_label.set_line_wrap(True)
            title_label.set_property('xalign', 0.5)
            box.pack_start(title_label, True, True, 0)
            title_label.show()
        if path is not None:
            alignment_box = Gtk.Alignment.new(xalign=0.5, yalign=0.5,
                                              xscale=0, yscale=0)
            box.pack_start(alignment_box, True, False, 5)
            image = Gtk.Image.new_from_file(path)
            alignment_box.add(image)
            image.show()
            alignment_box.show()
        if caption is not None:
            caption_label = Gtk.Label(
                '<span foreground="%s">%s</span>' %
                (style.COLOR_BUTTON_GREY.get_html(), caption))
            caption_label.set_use_markup(True)
            caption_label.set_line_wrap(True)
            caption_label.set_property('xalign', 0.5)
            box.pack_start(caption_label, True, True, 0)
            caption_label.show()
    return box


def get_favorites():
    favorites_path = env.get_profile_path('favorite_activities')
    if os.path.exists(favorites_path):
        favorites_data = json.load(open(favorites_path))
        favorites_list = favorites_data['favorites']
    return favorites_list


class Exercises():

    def __init__(self, activity):
        self._activity = activity
        self._current_task = None

        self._task_list = [EnterEmailTask(self._activity),
                           ChangeNickTask(self._activity),
                           RestoreNickTask(self._activity),
                           AddFavoriteTask(self._activity),
                           RemoveFavoriteTask(self._activity),
                           FinishedAllTasks(self._activity)]

    def get_help_info(self):
        _logger.debug('get_help_info for task %d' % self._current_task)
        if self._current_task is None:
            return (None, None)
        else:
            return self._task_list[self._current_task].get_help_info()

    def get_number_of_tasks(self):
        return len(self._task_list)

    def _run_task(self, task_number):
        ''' To run a task, we need a message to display,
            a task method to call that returns True or False,
            and perhaps some data '''

        prompt = self._task_list[task_number].get_prompt()
        data = self._task_list[task_number].get_data()
        test = self._task_list[task_number].test
        uid = self._task_list[task_number].uid
        graphics = self._task_list[task_number].get_graphics()
        success = self._task_list[task_number].get_success()
        retry = self._task_list[task_number].get_retry()
        title, help_file = self._task_list[task_number].get_help_info()

        if title is None or help_file is None:
            self._activity.help_button.set_sensitive(False)
        else:
            self._activity.help_button.set_sensitive(True)

        # Set up the task the first time through
        if self._current_task is None:
            self._current_task = self._activity.current_task
            if graphics is not None:
                self.scroll_window = Gtk.ScrolledWindow()
                self.scroll_window.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
                self.scroll_window.set_policy(Gtk.PolicyType.AUTOMATIC,
                                              Gtk.PolicyType.AUTOMATIC)
                self.scroll_window.add(graphics)
                graphics.show()
                self.scroll_window.show()
                self._activity.box.pack_start(self.scroll_window, True, True, 0)
                self._activity.prompt_window.hide()
                self._activity.box.show()

        task_data = self._activity.read_task_data(uid)
        if task_data is None:
            # self._activity.label_task(msg=prompt)
            task_data = {}
            task_data['start_time'] = time.time()
            task_data['task'] = prompt
            task_data['attempt'] = 0
            task_data['data'] = data
            self._activity.write_task_data(uid, task_data)

        GObject.timeout_add(5000, self._test, test, task_data,
                            uid, graphics, retry, success)

    def _test(self, test, task_data, uid, graphics, retry, success):
        if test(self, task_data):
            # Record end time
            task_data = self._activity.read_task_data(uid)
            task_data['end_time'] = time.time()
            self._activity.write_task_data(uid, task_data)

            self._current_task = None
            self._activity.current_task += 1
            self._activity.write_task_data('current_task',
                                           self._activity.current_task)
            if graphics is not None:
                self.scroll_window.destroy()
            self._activity.button_label.set_text(_('Continue to next task'))
            self._activity.prompt_window.show()
        else:
            task_data['attempt'] += 1
            self._activity.write_task_data(uid, task_data)
            self._run_task(self._activity.current_task)

    def task_master(self):
        _logger.debug('task master: running task %d' % 
                       (self._activity.current_task))
        # Do we have more tasks to run?
        if self._activity.current_task < len(self._task_list):
            self._run_task(self._activity.current_task)
        else:
            self._activity.complete = True
            self._activity.button_label.set_text(_('Finished!'))


class Task():
    ''' Generate class for defining tasks '''

    def __init__(self, activity):
        self.name = 'Generic Task'
        self.uid = None
        self._activity = activity

    def test(self, exercises, task_data):
        ''' The test to determine if task is completed '''
        raise NotImplementedError

    def get_success(self):
        ''' String to present to the user when task is completed '''
        return _('Success!')

    def get_retry(self):
        ''' String to present to the user when task is not completed '''
        return _('Keep trying')

    def get_data(self):
        ''' Any data needed for the test '''
        return None

    def get_prompt(self):
        ''' String to present to the user to define the task '''
        raise NotImplementedError

    def get_help_info(self):
        return (None, None)

    def get_graphics(self):
        ''' Graphics to present with the task '''
        return None


class EnterEmailTask(Task):

    def __init__(self, activity):
        self.name = _('Enter Email Task')
        self.uid = 'email'
        self.entries = [None]
        self._activity = activity

    def test(self, exercises, task_data):
        if self.entries[0] is None:
            return False
        else:
            self._activity.write_task_data('email_address',
                                           self.entries[0])
            return True

    def get_prompt(self):
        return _('Please enter your email address.')

    def get_graphics(self):
        return make_entry_graphic(
            self, [{'title': 'email address', 'caption': self.get_prompt()}])


class ChangeNickTask(Task):

    def __init__(self, activity):
        self.name = _('Change Nick Task')
        self.uid = 'nick1'
        self._activity = activity

    def test(self, exercises, task_data):
        if task_data['attempt'] == 0:
            _logger.debug('first attempt: saving nick value as %s' %
                          profile.get_nick_name())
            self._activity.write_task_data('nick', profile.get_nick_name())
            return False
        else:
            target = self._activity.read_task_data('nick')
            _logger.debug('%d attempt: comparing %s to %s' %
                          (task_data['attempt'], profile.get_nick_name(),
                           target))
            return not profile.get_nick_name() == target

    def get_prompt(self):
        return _('Change your nick')

    def get_help_info(self):
        return ('My Settings', 'my_settings.html')

    def get_graphics(self):
        file_path = os.path.join(os.path.expanduser('~'), 'Activities',
                                 'Help.activity', 'images',
                                 'Home_fav-menu.png')
        return make_image_graphic([{'title':self.get_prompt(),
                                    'path':file_path}])


class RestoreNickTask(Task):

    def __init__(self, activity):
        self.name = _('Restore Nick Task')
        self.uid = 'nick2'
        self._activity = activity
        self._target = self._activity.read_task_data('nick')

    def test(self, exercises, task_data):
        result = profile.get_nick_name() == self._target
        if result:
            self._activity.add_badge(
                _('Congratulations! You changed your nickname.'))
        return result

    def get_prompt(self):
        return _('Restore your nick to %s' % (self._target))

    def get_help_info(self):
        return ('My Settings', 'my_settings.html')

    def get_graphics(self):
        file_path = os.path.join(os.path.expanduser('~'), 'Activities',
                                 'Help.activity', 'images',
                                 'Home_fav-menu.png')
        return make_image_graphic([{'title':self.get_prompt(),
                                    'path':file_path}])


class AddFavoriteTask(Task):

    def __init__(self, activity):
        self.name = _('Add Favorite Task')
        self.uid = 'favorites1'
        self._activity = activity

    def test(self, exercises, task_data):
        if task_data['attempt'] == 0:
            _logger.debug('first attempt: saving favorites list')
            favorites_list = get_favorites()
            self._activity.write_task_data('favorites', len(favorites_list))
            return False
        else:
            favorites_count = len(get_favorites())
            saved_favorites_count = self._activity.read_task_data('favorites')
            return favorites_count > saved_favorites_count

    def get_prompt(self):
        return _('Add a favorite')

    def get_help_info(self):
        return ('Home', 'home_view.html')

    def get_graphics(self):
        file_path = os.path.join(os.path.expanduser('~'), 'Activities',
                                 'Help.activity', 'images',
                                 'Journal_main_annotated.png')
        return make_image_graphic([{'title':self.get_prompt(),
                                    'path':file_path}])
        '''
        url =  os.path.join(os.path.expanduser('~'), 'Activities',
                                 'Help.activity', 'html',
                                 'home_view.html')
        _logger.debug(url)
        return make_html_graphic('file://' + url)
        '''


class RemoveFavoriteTask(Task):

    def __init__(self, activity):
        self.name = _('Remove Favorite Task')
        self.uid = 'favorites2'
        self._activity = activity

    def test(self, exercises, task_data):
        if task_data['attempt'] == 0:
            favorites_list = get_favorites()
            self._activity.write_task_data('favorites', len(favorites_list))
            return False
        else:
            favorites_count = len(get_favorites())
            saved_favorites_count = self._activity.read_task_data('favorites')
            result = favorites_count < saved_favorites_count
            if result:
                self._activity.add_badge(
                    _('Congratulations! You changed your '
                      'favorite activities.'))
            return result

    def get_prompt(self):
        return _('Remove a favorite')

    def get_help_info(self):
        return ('Home', 'home_view.html')

    def get_graphics(self):
        file_path = os.path.join(os.path.expanduser('~'), 'Activities',
                                 'Help.activity', 'images',
                                 'Journal_main_annotated.png')
        return make_image_graphic([{'title':self.get_prompt(),
                                    'path':file_path}])


class FinishedAllTasks(Task):

    def __init__(self, activity):
        self.name = _('Finished All Tasks')
        self.uid = 'finished'
        self._activity = activity

    def test(self, exercises, task_data):
        self._activity.completed = True
        return True

    def get_prompt(self):
        return _('You are a Sugar Zenmaster.')
