import typing as t
from dataclasses import dataclass
from enum import auto, unique, IntEnum

import common.crypto as crypto
import common.types as types
import common.codec as codec
import common.errors as errors

_T = t.TypeVar("_T", bound="LogData")


@dataclass
class LogData:
    pass

    def encode(self) -> bytes:
        return codec.encode([])

    @classmethod
    def decode(cls: _T) -> _T:
        return LogData()


@dataclass
class RegisterLogData(LogData):
    pass


@dataclass
class PutPhotoLogData(LogData):
    photo_id: int

    def encode(self):
        return codec.encode(
            [
                self.photo_id,
            ]
        )

    @classmethod
    def decode(cls: _T, data: bytes) -> _T:
        (photo_id,) = codec.decode(data)
        return cls(photo_id)


@unique
class OperationCode(IntEnum):
    REGISTER = auto()
    PUT_PHOTO = auto()


class LogEntry:
    def __init__(
        self,
        opcode: OperationCode,
        data: bytes,
    ) -> None:
        """
        Generates a new log entry with the given data
        """
        self.opcode = opcode.value
        self.data = data

    def __str__(self) -> str:
        return f"LogEntry(opcode={OperationCode(self.opcode)}, data={self.data})"

    def encode(self) -> bytes:
        """
        Encode this log entry and the contained data, and return
        a bytestring that represents the whole thing.
        """
        result = codec.encode(
            [
                self.opcode,
                self.data,
            ]
        )
        return result

    @staticmethod
    def decode(data: bytes) -> "LogEntry":
        """
        Decode this log entry and the contained data
        """
        opcode_int, log_data = codec.decode(data)
        opcode = OperationCode(opcode_int)
        return LogEntry(opcode, log_data)

    def data_hash(self) -> bytes:
        return crypto.data_hash(self.encode())

