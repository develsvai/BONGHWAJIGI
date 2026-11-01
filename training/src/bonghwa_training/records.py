"""TensorFlow 런타임 없이 공개 Example protobuf와 CRC가 있는 TFRecord를 읽는다."""

import struct
from pathlib import Path

import google_crc32c
import numpy as np
from google.protobuf import descriptor_pb2, descriptor_pool, message_factory


def example_class():
    file = descriptor_pb2.FileDescriptorProto(name="bonghwa_example.proto", package="tensorflow")
    file.syntax = "proto3"
    float_list = file.message_type.add(name="FloatList")
    float_list.field.add(name="value", number=1, label=3, type=2)
    feature = file.message_type.add(name="Feature")
    feature.field.add(
        name="float_list", number=2, label=1, type=11, type_name=".tensorflow.FloatList"
    )
    features = file.message_type.add(name="Features")
    entry = features.nested_type.add(name="FeatureEntry")
    entry.options.map_entry = True
    entry.field.add(name="key", number=1, label=1, type=9)
    entry.field.add(name="value", number=2, label=1, type=11, type_name=".tensorflow.Feature")
    features.field.add(
        name="feature", number=1, label=3, type=11, type_name=".tensorflow.Features.FeatureEntry"
    )
    example = file.message_type.add(name="Example")
    example.field.add(name="features", number=1, label=1, type=11, type_name=".tensorflow.Features")
    pool = descriptor_pool.DescriptorPool()
    pool.Add(file)
    return message_factory.GetMessageClass(pool.FindMessageTypeByName("tensorflow.Example"))


Example = example_class()


def masked_crc32c(data: bytes) -> int:
    value = google_crc32c.value(data)
    return (((value >> 15) | (value << 17)) + 0xA282EAD8) & 0xFFFFFFFF


def iter_records(path: Path):
    with path.open("rb") as source:
        index = 0
        while length_bytes := source.read(8):
            if len(length_bytes) != 8:
                raise ValueError("잘린 TFRecord 길이입니다.")
            length_crc = source.read(4)
            if len(length_crc) != 4 or struct.unpack("<I", length_crc)[0] != masked_crc32c(
                length_bytes
            ):
                raise ValueError("TFRecord 길이 CRC가 일치하지 않습니다.")
            length = struct.unpack("<Q", length_bytes)[0]
            if not 0 < length <= 2 * 1024 * 1024:
                raise ValueError("예상한 산불 패치의 레코드 크기가 아닙니다.")
            data = source.read(length)
            crc = source.read(4)
            if (
                len(data) != length
                or len(crc) != 4
                or struct.unpack("<I", crc)[0] != masked_crc32c(data)
            ):
                raise ValueError("잘리거나 CRC가 불일치하는 TFRecord입니다.")
            message = Example.FromString(data)
            arrays = {
                key: np.asarray(value.float_list.value, dtype=np.float32)
                for key, value in message.features.feature.items()
            }
            yield index, arrays
            index += 1
