# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# NO CHECKED-IN PROTOBUF GENCODE
# source: system.proto
# Protobuf Python Version: 5.29.0
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(
    _runtime_version.Domain.PUBLIC,
    5,
    29,
    0,
    '',
    'system.proto'
)
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from google.protobuf import empty_pb2 as google_dot_protobuf_dot_empty__pb2


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x0csystem.proto\x12\x07machine\x1a\x1bgoogle/protobuf/empty.proto\"3\n\x07Message\x12\x11\n\tsender_id\x18\x01 \x01(\x05\x12\x15\n\rlogical_clock\x18\x02 \x01(\x05\x32\x85\x01\n\x0bPeerService\x12\x37\n\x0bSendMessage\x12\x10.machine.Message\x1a\x16.google.protobuf.Empty\x12=\n\x0fReceiveMessages\x12\x16.google.protobuf.Empty\x1a\x10.machine.Message0\x01\x62\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'system_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
  DESCRIPTOR._loaded_options = None
  _globals['_MESSAGE']._serialized_start=54
  _globals['_MESSAGE']._serialized_end=105
  _globals['_PEERSERVICE']._serialized_start=108
  _globals['_PEERSERVICE']._serialized_end=241
# @@protoc_insertion_point(module_scope)
