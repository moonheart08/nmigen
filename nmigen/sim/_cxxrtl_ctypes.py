from enum import IntEnum
from ctypes import (cdll, Structure, POINTER, CFUNCTYPE,
                    c_int, c_size_t, c_uint32, c_uint64, c_void_p, c_char_p,
                    byref)


__all__ = []


class _toplevel(Structure):
    pass


cxxrtl_toplevel = POINTER(_toplevel)


class _cxxrtl_handle(Structure):
    pass


cxxrtl_handle = POINTER(_cxxrtl_handle)


class cxxrtl_type(IntEnum):
    VALUE  = 0
    WIRE   = 1
    MEMORY = 2
    ALIAS  = 3


class cxxrtl_object(Structure):
    _fields_ = [
        ("_type",   c_uint32),
        ("width",   c_size_t),
        ("lsb_at",  c_size_t),
        ("depth",   c_size_t),
        ("zero_at", c_size_t),
        ("_curr",   POINTER(c_uint32)),
        ("_next",   POINTER(c_uint32)),
    ]

    @property
    def type(self):
        return type(self._type)

    @property
    def chunks(self):
        return ((self.width + 31) // 32) * self.depth

    @property
    def curr(self):
        value = 0
        for chunk in range(self.chunks):
            value <<= 32
            value |= self._curr[chunk]
        return value << self.lsb_at

    @curr.setter
    def curr(self, value):
        value = (value >> self.lsb_at) & ((1 << self.width) - 1)
        for chunk in range(self.chunks):
            self._curr[chunk] = value & 0xffffffff
            value >>= 32

    @property
    def next(self):
        value = 0
        for chunk in range(self.chunks):
            value <<= 32
            value |= self._next[chunk]
        return value << self.lsb_at

    @next.setter
    def next(self, value):
        value = (value >> self.lsb_at) & ((1 << self.width) - 1)
        for chunk in range(self.chunks):
            self._next[chunk] = value & 0xffffffff
            value >>= 32


cxxrtl_object_p = POINTER(cxxrtl_object)
cxxrtl_enum_callback_fn = CFUNCTYPE(c_void_p, cxxrtl_object_p, c_size_t)


class _cxxrtl_vcd(Structure):
    pass


cxxrtl_vcd = POINTER(_cxxrtl_vcd)
cxxrtl_vcd_filter_fn = CFUNCTYPE(c_void_p, c_char_p, cxxrtl_object_p)


class cxxrtl_library:
    def __init__(self, filename, *, design_name="cxxrtl_design"):
        self._library = library = cdll.LoadLibrary(filename)

        self.design_create = getattr(library, f"{design_name}_create")
        self.design_create.argtypes = []
        self.design_create.restype = cxxrtl_toplevel

        self.create = library.cxxrtl_create
        self.create.argtypes = [cxxrtl_toplevel]
        self.create.restype = cxxrtl_handle

        self.destroy = library.cxxrtl_destroy
        self.destroy.argtypes = [cxxrtl_handle]
        self.destroy.restype = None

        self.eval = library.cxxrtl_eval
        self.eval.argtypes = [cxxrtl_handle]
        self.eval.restype = c_int

        self.commit = library.cxxrtl_commit
        self.commit.argtypes = [cxxrtl_handle]
        self.commit.restype = c_int

        self.step = library.cxxrtl_step
        self.step.argtypes = [cxxrtl_handle]
        self.step.restype = None

        _get_parts = library.cxxrtl_get_parts
        _get_parts.argtypes = [cxxrtl_handle, c_char_p, POINTER(c_size_t)]
        _get_parts.restype = cxxrtl_object_p
        def get_parts(handle, name):
            count = c_size_t()
            parts = _get_parts(handle, name, byref(count))
            if parts:
                return [parts[n] for n in range(count.value)]
        self.get_parts = get_parts

        self.enum = library.cxxrtl_enum
        self.enum.argtypes = [cxxrtl_handle, c_void_p, cxxrtl_enum_callback_fn]
        self.enum.restype = None

        self.vcd_create = library.cxxrtl_vcd_create
        self.vcd_create.argtypes = []
        self.vcd_create.restype = cxxrtl_vcd

        self.vcd_destroy = library.cxxrtl_vcd_destroy
        self.vcd_destroy.argtypes = [cxxrtl_vcd]
        self.vcd_destroy.restype = None

        self.vcd_add = library.cxxrtl_vcd_add
        self.vcd_add.argtypes = [cxxrtl_vcd, c_int, c_char_p]
        self.vcd_add.restype = None

        self.vcd_add_from = library.cxxrtl_vcd_add_from
        self.vcd_add_from.argtypes = [cxxrtl_vcd, cxxrtl_handle]
        self.vcd_add_from.restype = None

        self.vcd_add_from_if = library.cxxrtl_vcd_add_from_if
        self.vcd_add_from_if.argtypes = [cxxrtl_vcd, cxxrtl_handle, c_void_p, cxxrtl_vcd_filter_fn]
        self.vcd_add_from_if.restype = None

        self.vcd_add_from_without_memories = library.cxxrtl_vcd_add_from_without_memories
        self.vcd_add_from_without_memories.argtypes = [cxxrtl_vcd, cxxrtl_handle]
        self.vcd_add_from_without_memories.restype = None

        self.vcd_sample = library.cxxrtl_vcd_sample
        self.vcd_sample.argtypes = [cxxrtl_vcd, c_uint64]
        self.vcd_sample.restype = None

        self.vcd_read = library.cxxrtl_vcd_read
        self.vcd_read.argtypes = [cxxrtl_vcd, POINTER(c_char_p), POINTER(c_size_t)]
        self.vcd_read.restype = None