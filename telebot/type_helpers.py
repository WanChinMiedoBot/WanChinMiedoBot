import six
import json

import telegram_types as types


class KeyboardHelper:
    """
    Helper class to construct a ReplyKeyboardMarkup object.
    Basic usage:
        >>> keyboard = KeyboardHelper().add("A").add("B").add("C").new_row().add("D").add("E").build()
        >>> another = KeyboardHelper().add("Send location", request_location=True).build(selective=True)
    """

    def __init__(self):
        self.keyboard = [[]]

    def __add(self, item):
        self.keyboard[-1].append(item)

    def add(self, text, **kwargs):
        """
        Add a new button to the current row.

        :param text: Text of the button. If none of the optional fields are used,
                    it will be sent to the bot as a message when the button is pressed
        :param kwargs: Optional values to be passed to the KeyboardButton constructor
        :return: KeyboardHelper self for method chaining
        """
        self.keyboard[-1].append(types.KeyboardButton(text, **kwargs))
        return self

    def new_row(self):
        """
        Switch to a new row.
        :return: KeyboardHelper self for method chaining
        """
        self.keyboard.append([])
        return self

    def build(self, **kwargs):
        """
        Build the ReplyKeyboardMarkup object.

        :param kwargs: Any optional arguments to be passed to the ReplyKeyboardMarkup constructor
        :return: types.ReplyKeyboardMarkup
        """
        return types.ReplyKeyboardMarkup(self.keyboard, **kwargs)


class InlineKeyboardHelper:
    """
    Helper class to construct an InlineKeyboardMarkup object.
    Basic usage:
        >>> keyboard = InlineKeyboardHelper().add("A").add("B").add("C").new_row().add("D").add("E").build()
        >>> another = InlineKeyboardHelper().add("Visit site", url="http://telegram.org").build(selective=True)
    """

    def __init__(self):
        self.keyboard = [[]]

    def add(self, text, **kwargs):
        """
        Add a new button to the current row.

        :param text: Label text on the button
        :param kwargs: Optional values to be passed to the InlineKeyboardButton constructor
        :return: KeyboardHelper self for method chaining
        """
        self.keyboard[-1].append(types.InlineKeyboardButton(text, **kwargs))
        return self

    def new_row(self):
        """
        Switch to a new row.
        :return: KeyboardHelper self for method chaining
        """
        self.keyboard.append([])
        return self

    def build(self):
        """
        Build the InlineReplyKeyboardMarkup object.
        :return: types.ReplyKeyboardMarkup
        """
        return types.InlineKeyboardMarkup(self.keyboard)


class InlineQueryResultHelper:
    TYPES = [
        'article', 'audio', 'contact', 'document', 'gif', 'location',
        'mpeg4_gif', 'photo', 'venue', 'video', 'voice'
    ]
    CACHED_TYPES = ['photo', 'gif', 'mpeg4_gif', 'sticker', 'document', 'video', 'voice', 'audio']
    __CACHED_FILE_ID_KEYS = {
        'photo': 'photo_file_id',
        'gif': 'gif_file_id',
        'mpeg4_gif': 'mpeg4_file_id',
        'sticker': 'sticker_file_id',
        'document': 'document_file_id',
        'video': 'video_file_id',
        'voice': 'voice_file_id',
        'audio': 'audio_file_id'
    }

    def __init__(self):
        raise NotImplementedError('Instantiation not allowed')

    @classmethod
    def create_result(cls, type, id, **kwargs):
        if type not in cls.TYPES:
            raise ValueError('Unknown type: {0}. Known types: {1}'.format(type, cls.TYPES))

        json_dict = kwargs
        json_dict['type'] = type
        json_dict['id'] = id

        for k, v in six.iteritems(json_dict):
            json_dict[k] = types.to_dict(v)

        return json_dict

    @classmethod
    def create_cached_result(cls, type, id, file_id, **kwargs):
        if type not in cls.CACHED_TYPES:
            raise ValueError('Unknown cached type: {0}. Known types: {1}'.format(type, cls.CACHED_TYPES))

        json_dict = kwargs
        json_dict['type'] = type
        json_dict['id'] = id
        json_dict[cls.__CACHED_FILE_ID_KEYS[type]] = file_id

        for k, v in six.iteritems(json_dict):
            json_dict[k] = types.to_dict(v)

        return json_dict


class InlineQueryResultsBuilder:

    def __init__(self):
        self.results = []

    def add(self, type, id, **kwargs):
        self.results.append(InlineQueryResultHelper.create_result(type, id, **kwargs))

    def add_cached(self, type, id, file_id, **kwargs):
        self.results.append(InlineQueryResultHelper.create_cached_result(type, id, file_id, **kwargs))

    def build(self):
        return json.dumps(self.results)
