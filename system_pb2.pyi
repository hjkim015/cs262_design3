from google.protobuf import empty_pb2 as _empty_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class Message(_message.Message):
    __slots__ = ("sender_id", "logical_clock")
    SENDER_ID_FIELD_NUMBER: _ClassVar[int]
    LOGICAL_CLOCK_FIELD_NUMBER: _ClassVar[int]
    sender_id: int
    logical_clock: int
    def __init__(self, sender_id: _Optional[int] = ..., logical_clock: _Optional[int] = ...) -> None: ...
