# -*- coding: utf-8 -*-
import re
import six
import types

from telebot import util


def same_chat(chat):
    return lambda message: message.chat.id == chat.id


def has_content_types(content_types):
    return lambda m: m.content_type in content_types


def has_commands(commands):
    return lambda m: m.content_type == 'text' and util.extract_command(m.text) in commands


def has_regex(regex):
    return lambda m: m.content_type == 'text' and re.search(regex, m.text)


class EventBus:

    def __init__(self):
        self.event_listeners = {}

    def prepend_event_listener(self, event, listener):
        if event in self.event_listeners:
            self.event_listeners[event].insert(0, listener)
        else:
            self.event_listeners[event] = [listener]

    def append_event_listener(self, event, listener):
        if event in self.event_listeners:
            self.event_listeners[event].append(listener)
        else:
            self.event_listeners[event] = [listener]

    def remove_event_listener(self, listener):
        for event, event_listeners in six.iteritems(self.event_listeners):
            if listener in event_listeners:
                event_listeners.remove(listener)
                return True
        return False

    def dispatch(self, event, *args, **kwargs):
        if event not in self.event_listeners:
            util.logger.debug("Event {0} dispatched but no listeners".format(event))
            return

        for listener in self.event_listeners[event]:
            if listener(*args, **kwargs):
                break


class GeneratorListener:

    def __init__(self, event_bus, chat_id, generator):
        self.event_bus = event_bus
        self.chat_id = chat_id
        self.generator = generator

    def __call__(self, message):
        if message.chat.id != self.chat_id:
            return False

        try:
            self.generator.send(message)
        except StopIteration:
            self.event_bus.remove_event_listener(self)
        return True


class MessageHandler:

    def __init__(self, event_bus, handler, commands=None, regexp=None, func=None, content_types=None):
        self.event_bus = event_bus

        self.handler = handler
        self.tests = []
        if content_types is not None:
            self.tests.append(has_content_types(content_types))

        if commands is not None:
            self.tests.append(has_commands(commands))

        if regexp is not None:
            self.tests.append(has_regex(regexp))

        if func is not None:
            self.tests.append(func)

    def __call__(self, message):
        if not all([test(message) for test in self.tests]):
            return False

        returned = self.handler(message)
        if isinstance(returned, types.GeneratorType):
            returned.next()
            generator_listener = GeneratorListener(self.event_bus, message.chat.id, returned)
            self.event_bus.prepend_event_listener('on_message', generator_listener)
        return True


class InlineHandler:

    def __init__(self, handler, func):
        self.handler = handler
        self.func = func

    def __call__(self, inline_query):
        if self.func(inline_query):
            return self.handler(inline_query)


class ChosenInlineResultHandler:

    def __init__(self, handler, func):
        self.handler = handler
        self.func = func

    def __call__(self, chosen_inline_result):
        if self.func(chosen_inline_result):
            return self.handler(chosen_inline_result)


class CallbackQueryHandler:

    def __init__(self, handler, func):
        self.handler = handler
        self.func = func

    def __call__(self, callback_query):
        if self.func(callback_query):
            self.handler(callback_query)
