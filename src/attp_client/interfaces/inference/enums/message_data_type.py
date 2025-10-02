from enum import Enum


class MessageDataTypeEnum(Enum):
    """
    Enumeration for data types available to be sent by users/AI
    """

    JPEG_IMAGE = 'jpeg_image'  # .jpeg .jpg
    FFMPEG_VIDEO = 'ffmpeg_video'  # mp4
    PLAIN_TEXT = 'plain_text'  # txt, that would be also a simple chat message
    WAVE_AUDIO = 'wave_audio'  # wav
    PLACEHOLDER_KEY = 'placeholder_key'
    NONE = 'none'
