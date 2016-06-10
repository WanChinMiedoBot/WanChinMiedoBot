# -*- coding: utf-8 -*-
import pytest
import mock

from telebot import listeners


class TestEventBus:

    def test_dispatch_no_listeners(self):
        bus = listeners.EventBus()
        assert not bus.dispatch('some_event')

    def test_listener_accepts(self):
        bus = listeners.EventBus()
        bus.append_event_listener('some_event', lambda: True)
        assert bus.dispatch('some_event')

    def test_listeners_rejects(self):
        bus = listeners.EventBus()
        bus.append_event_listener('some_event', lambda: False)
        assert not bus.dispatch('some_event')

    def test_only_one_called(self):
        bus = listeners.EventBus()
        first_listener = mock.MagicMock(return_value=True)
        second_listener = mock.MagicMock(return_value=True)

        bus.append_event_listener('some_event', first_listener)
        bus.append_event_listener('some_event', second_listener)
        bus.dispatch('some_event')

        first_listener.assert_called_once()
        second_listener.assert_not_called()

    def test_prioritized(self):
        bus = listeners.EventBus()
        first_listener = mock.MagicMock(return_value=True)
        second_listener = mock.MagicMock(return_value=True)

        bus.append_event_listener('some_event', first_listener)
        bus.prepend_event_listener('some_event', second_listener)
        bus.dispatch('some_event')

        first_listener.assert_not_called()
        second_listener.assert_called_once()
