# -*- coding: utf-8 -*-
import telebot.listeners as listeners
from telebot.util import logger
from telebot.apihelper import TelegramApiInterface, DefaultRequestExecutor


def stopping_exception_handler(_):
    logger.exception("Exception occurred. Stopping.")
    return False


def continuing_exception_handler(_):
    logger.exception("Exception occurred.")
    return True


class TeleBot(TelegramApiInterface):

    def __init__(self, token, exception_handler=stopping_exception_handler, request_executor=None):
        """
        :param token: bot API token
        :return: Telebot object.
        """
        request_executor = request_executor if request_executor is not None else DefaultRequestExecutor()
        TelegramApiInterface.__init__(self, token, request_executor)

        self.exception_handler = exception_handler
        self.token = token
        self.event_bus = listeners.EventBus()

        self.__stop_polling = False
        self.last_update_id = 0

    def __yield_updates(self, timeout=20):
        updates = self.get_updates(offset=self.last_update_id, timeout=timeout)
        while updates:
            for u in updates:
                yield u
            self.last_update_id = max(updates, key=lambda update: update.update_id).update_id
            updates = self.get_updates(offset=(self.last_update_id + 1), timeout=timeout)

    def skip_updates(self, timeout=1):
        """
        Get and discard all pending updates before first poll of the bot
        This method may take up to `timeout` seconds to execute.
        :return: A list of all skipped updates
        :rtype list[types.Update]
        """
        return list(self.__yield_updates(timeout=timeout))

    def retrieve_updates(self, timeout=20):
        """
        Retrieves updates from Telegram and notifies listeners.
        Does not catch any exceptions raised by listeners.
        """
        self.process_new_updates(self.__yield_updates(timeout=timeout))

    def __process_update(self, update):
        logger.debug("Processing update {0}".format(update))

        self.event_bus.dispatch('on_update', update)

        if update.message is not None:
            self.event_bus.dispatch('on_message', update.message)
        elif update.edited_message is not None:
            self.event_bus.dispatch('on_edited_message', update.edited_message)
        elif update.inline_query is not None:
            self.event_bus.dispatch('on_inline_query', update.inline_query)
        elif update.chosen_inline_result is not None:
            self.event_bus.dispatch('on_chosen_inline_result', update.chosen_inline_result)
        elif update.callback_query is not None:
            self.event_bus.dispatch('on_callback_query', update.callback_query)

    def process_new_updates(self, updates):
        for update in updates:
            try:
                self.__process_update(update)
            except Exception as e:
                # If the exception handler returns False, drop all updates
                if not self.exception_handler(e):
                    self.stop_polling()
                    break

    def polling(self, skip_pending=False, timeout=20):
        """
        This function retrieves Updates and dispatches events.

        Warning: Do not call this function more than once!

        :param skip_pending: Retrieve and discard pending updates (e.g. do not dispatch events)
        :param timeout: Timeout in seconds for long polling.
        :return:
        """
        logger.info('Started polling.')
        self.__stop_polling = False

        if skip_pending:
            logger.info('Skipped {0} pending updates'.format(len(self.skip_updates())))

        while not self.__stop_polling:
            self.retrieve_updates(timeout)

        logger.info('Stopped polling.')

    def stop_polling(self):
        self.__stop_polling = True

    def remove_webhook(self):
        return self.set_webhook()  # No params resets webhook

    def reply_to(self, message, text, **kwargs):
        """
        Convenience function for `send_message(message.chat.id, text, reply_to_message_id=message.message_id, **kwargs)`
        """
        return self.send_message(message.chat.id, text, reply_to_message_id=message.message_id, **kwargs)

    def message_handler(self, **kwargs):
        """
        Message handler decorator.
        This decorator can be used to decorate functions that must handle certain types of messages.
        All message handlers are tested in the order they were added.

        Example:

        bot = TeleBot('TOKEN')

        # Handles all messages which text matches regexp.
        @bot.message_handler(regexp='someregexp')
        def command_help(message):
            bot.send_message(message.chat.id, 'Did someone call for help?')

        # Handle all sent documents of type 'text/plain'.
        @bot.message_handler(func=lambda message: message.document.mime_type == 'text/plain', content_types=['document'])
        def command_handle_document(message):
            bot.send_message(message.chat.id, 'Document received, sir!')

        # Handle all other commands.
        @bot.message_handler(func=lambda message: True, content_types=['audio', 'video', 'document', 'text', 'location', 'contact', 'sticker'])
        def default_command(message):
            bot.send_message(message.chat.id, "This is the default command handler.")

        :param commands:
        :param regexp: Optional regular expression.
        :param func: Optional lambda function. The lambda receives the message to test as the first parameter. It must return True if the command should handle the message.
        :param content_types: This commands' supported content types. Must be a list. Defaults to ['text'].
        """
        def decorator(handler):
            self.add_message_handler(handler, **kwargs)
            return handler
        return decorator

    def add_message_handler(self, handler, **kwargs):
        self.event_bus.append_event_listener('on_message', listeners.MessageHandler(self.event_bus, handler, **kwargs))

    def inline_handler(self, func):
        def decorator(handler):
            self.add_inline_handler(handler, func)
            return handler
        return decorator

    def add_inline_handler(self, handler, func):
        self.event_bus.append_event_listener('on_inline_query', listeners.InlineHandler(handler, func))

    def chosen_inline_handler(self, func):
        def decorator(handler):
            self.add_chosen_inline_handler(handler, func)
            return handler
        return decorator

    def add_chosen_inline_handler(self, handler, func):
        self.event_bus.append_event_listener('on_chosen_inline_result', listeners.ChosenInlineResultHandler(handler, func))

    def callback_query_handler(self, func):
        def decorator(handler):
            self.add_callback_query_handler(handler, func)
            return handler
        return decorator

    def add_callback_query_handler(self, handler, func):
        self.event_bus.append_event_listener('on_callback_query', listeners.CallbackQueryHandler(handler, func))


