"""Pure-python wrapper for librsvg that has no dependencies on anything Gtk-related."""
#+
# Copyright 2017 Lawrence D'Oliveiro <ldo@geek-central.gen.nz>.
# Licensed under the GNU Lesser General Public License v2.1 or later.
#-

from numbers import \
    Real
import ctypes as ct
from weakref import \
    WeakValueDictionary
import array
import atexit
import qahirah as qah
from qahirah import \
    Vector

rsvg = ct.cdll.LoadLibrary("librsvg-2.so.2")
libc = ct.cdll.LoadLibrary("libc.so.6")

class RSVG :
    "useful definitions adapted from the librsvg includes. You will need to use the" \
    " constants, but apart from that, see the more Pythonic wrappers defined outside this" \
    " class in preference to accessing low-level structures directly."

    MAJOR_VERSION = 2
    MINOR_VERSION = 40
    MICRO_VERSION = 40
    VERSION = "2.40.18"

    gboolean = ct.c_int
    gsize = ct.c_ulong
    GType = ct.c_uint

    HandleFlags = ct.c_uint
    HANDLE_FLAGS_NONE = 0
    HANDLE_FLAG_UNLIMITED = 1 << 0
    HANDLE_FLAG_KEEP_IMAGE_DATA = 1 << 1

    GQuark = ct.c_uint

    class GError(ct.Structure) :
        pass
    #end GError
    GError._fields_ = \
        [
            ("domain", GQuark),
            ("code", ct.c_int),
            ("message", ct.c_char_p),
        ]
    GErrorPtr = ct.POINTER(GError)

    class DimensionData(ct.Structure) :
        _fields_ = \
            [
                ("width", ct.c_int),
                ("height", ct.c_int),
                ("em", ct.c_double), # seems to duplicate width, according to source code
                ("ex", ct.c_double), # seems to duplicate height
            ]
    #end DimensionData

    class PositionData(ct.Structure) :
        _fields_ = \
            [
                ("x", ct.c_int),
                ("y", ct.c_int),
            ]
    #end PositionData

    DEFAULT_DPI = 90 # from rsvg-base.c

#end RSVG

#+
# Routine arg/result types
#-

rsvg.rsvg_error_quark.restype = RSVG.GQuark
rsvg.rsvg_error_quark.argtypes = ()
rsvg.rsvg_error_get_type.restype = RSVG.GType
rsvg.rsvg_error_get_type.argtypes = ()

rsvg.rsvg_set_default_dpi.restype = None
rsvg.rsvg_set_default_dpi.argtypes = (ct.c_double,)
rsvg.rsvg_set_default_dpi_x_y.restype = None
rsvg.rsvg_set_default_dpi_x_y.argtypes = (ct.c_double, ct.c_double)

rsvg.rsvg_handle_set_dpi.restype = None
rsvg.rsvg_handle_set_dpi.argtypes = (ct.c_void_p, ct.c_double)
rsvg.rsvg_handle_set_dpi_x_y.restype = None
rsvg.rsvg_handle_set_dpi_x_y.argtypes = (ct.c_void_p, ct.c_double, ct.c_double)

rsvg.rsvg_handle_new.restype = ct.c_void_p
rsvg.rsvg_handle_new.argtypes = ()

rsvg.rsvg_handle_write.restype = RSVG.gboolean
rsvg.rsvg_handle_write.argtypes = (ct.c_void_p, ct.c_void_p, RSVG.gsize, RSVG.GErrorPtr)
rsvg.rsvg_handle_close.restype = RSVG.gboolean
rsvg.rsvg_handle_close.argtypes = (ct.c_void_p, RSVG.GErrorPtr)
# rsvg_handle_get_pixbuf, rsvg_handle_get_pixbuf_sub NYI

rsvg.rsvg_handle_get_base_uri.restype = ct.c_char_p
rsvg.rsvg_handle_get_base_uri.argtypes = (ct.c_void_p,)
rsvg.rsvg_handle_set_base_uri.restype = None
rsvg.rsvg_handle_set_base_uri.argtypes = (ct.c_void_p, ct.c_char_p)

rsvg.rsvg_handle_get_dimensions.restype = None
rsvg.rsvg_handle_get_dimensions.argtypes = (ct.c_void_p, ct.c_void_p)
rsvg.rsvg_handle_get_dimensions_sub.restype = RSVG.gboolean
rsvg.rsvg_handle_get_dimensions_sub.argtypes = (ct.c_void_p, ct.c_void_p, ct.c_char_p)
rsvg.rsvg_handle_get_position_sub.restype = RSVG.gboolean
rsvg.rsvg_handle_get_position_sub.argtypes = (ct.c_void_p, ct.c_void_p, ct.c_char_p)
rsvg.rsvg_handle_has_sub.restype = RSVG.gboolean
rsvg.rsvg_handle_has_sub.argtypes = (ct.c_void_p, ct.c_char_p)

rsvg.rsvg_handle_get_title.restype = ct.c_char_p
rsvg.rsvg_handle_get_title.argtypes = (ct.c_void_p,)
rsvg.rsvg_handle_get_desc.restype = ct.c_char_p
rsvg.rsvg_handle_get_desc.argtypes = (ct.c_void_p,)
rsvg.rsvg_handle_get_metadata.restype = ct.c_char_p
rsvg.rsvg_handle_get_metadata.argtypes = (ct.c_void_p,)

rsvg.rsvg_handle_new_with_flags.restype = ct.c_void_p
rsvg.rsvg_handle_new_with_flags.argtypes = (RSVG.HandleFlags,)

# GFile stuff NYI

rsvg.rsvg_handle_new_from_data.restype = ct.c_void_p
rsvg.rsvg_handle_new_from_data.argtypes = (ct.c_void_p, ct.c_ulong, RSVG.GErrorPtr)
rsvg.rsvg_handle_new_from_file.restype = ct.c_void_p
rsvg.rsvg_handle_new_from_file.argtypes = (ct.c_char_p, RSVG.GErrorPtr)

rsvg.rsvg_handle_free.restype = None
rsvg.rsvg_handle_free.argtypes = (ct.c_void_p,)
  # may be deprecated, but I don’t want to bring in any GLib/GObject dependencies

rsvg.rsvg_handle_render_cairo.restype = RSVG.gboolean
rsvg.rsvg_handle_render_cairo.argtypes = (ct.c_void_p, ct.c_void_p)
rsvg.rsvg_handle_render_cairo_sub.restype = RSVG.gboolean
rsvg.rsvg_handle_render_cairo_sub.argtypes = (ct.c_void_p, ct.c_void_p, ct.c_char_p)

libc.free.argtypes = (ct.c_void_p,)

#+
# Higher-level stuff begins here
#-

def set_default_dpi(dpi = 0) :
    if isinstance(dpi, Real) :
        rsvg.rsvg_set_default_dpi(dpi)
    elif isinstance(dpi, (Vector, tuple, list)) :
        dpi = Vector.from_tuple(dpi)
        rsvg.rsvg_set_default_dpi_x_y(dpi.x, dpi.y)
    else :
        raise TypeError("dpi must be a Real or a Vector")
    #end if
#end set_default_dpi

class Error :
    "wraps a GError."

    __slots__ = ("_error",)

    def __init__(self) :
        self._error = RSVG.GError()
    #end __init__

    @classmethod
    def init(celf) :
        "for consistency with other classes that don’t want caller to instantiate directly."
        return \
            celf()
    #end init

    def __del__(self) :
        libc.free(self._error.message)
        self._error.message = None
    #end __del__

    @property
    def domain(self) :
        return \
            self._error.domain
    #end domain

    @property
    def code(self) :
        return \
            self._error.code
    #end code

    @property
    def message(self) :
        return \
            self._error.message.decode()
    #end message

    def raise_if_set(self) :
        if self._error.code != 0 or self._error.domain != 0 :
            raise RuntimeError \
              (
                    "RSVG error code %#008x domain %#08x: %s"
                %
                    (
                        self._error.code,
                        self._error.domain,
                        (lambda : "?", lambda : self._error.message.decode())[self._error.message != None]()
                    )
              )
        #end if
    #end raise_if_set

#end Error

class _DummyError :
    # like an Error, but is never set and so will never raise.

    def raise_if_set(self) :
        pass
    #end raise_if_set

#end _DummyError

def _get_error(error) :
    # Common routine which processes an optional user-supplied Error
    # argument, and returns 2 Error-like objects: the first a real
    # Error object to be passed to the librsvg call, the second is
    # either the same Error object or a separate _DummyError object
    # on which to call raise_if_set() afterwards. The procedure for
    # using this is
    #
    #     error, my_error = _get_error(error)
    #     ... call librsvg routine, passing error._error ...
    #     my_error.raise_if_set()
    #
    # If the user passes None for error, then an internal Error object
    # is created, and returned as both results. That way, if it is
    # filled in by the librsvg call, calling raise_if_set() will
    # automatically raise the exception.
    # But if the user passed their own Error object, then it is
    # returned as the first result, and a _DummyError as the second
    # result. This means the raise_if_set() call becomes a noop, and
    # it is up to the caller to check if their Error object was filled
    # in or not.
    if error != None and not isinstance(error, Error) :
        raise TypeError("error must be an Error")
    #end if
    if error != None :
        my_error = _DummyError()
    else :
        my_error = Error()
        error = my_error
    #end if
    return \
        error, my_error
#end _get_error

class Handle :
    "an SVG rendering context. Do not instantiate directly; use the new_xxx methods."

    __slots__ = ("_rsvgobj", "__weakref__") # to forestall typos

    _instances = WeakValueDictionary()

    def __new__(celf, _rsvgobj) :
        self = celf._instances.get(_rsvgobj)
        if self == None :
            self = super().__new__(celf)
            self._rsvgobj = _rsvgobj
            celf._instances[_rsvgobj] = self
        else :
            rsvg.rsvg_handle_free(self._rsvgobj)
              # lose extra reference created by caller
        #end if
        return \
            self
    #end __new__

    @classmethod
    def new(celf, flags = None) :
        if flags != None :
            rsvgobj = rsvg.rsvg_handle_new_with_flags(flags)
        else :
            rsvgobj = rsvg.rsvg_handle_new()
        #end if
        return \
            celf(rsvgobj)
    #end new
    new_with_flags = new # whichever name you prefer

    @classmethod
    def new_from_data(celf, data, error = None) :
        if isinstance(data, bytes) :
            baseadr = ct.cast(data, ct.c_void_p).value
            length = len(data)
        elif isinstance(data, bytearray) :
            baseadr = ct.addressof((ct.c_char * len(data)).from_buffer(data))
            length = len(data)
        elif isinstance(data, array.array) and data.typecode == "B" :
            baseadr, length = data.buffer_info()
        else :
            raise TypeError("data is not bytes, bytearray or array.array of bytes")
        #end if
        error, my_error = _get_error(error)
        rsvgobj = rsvg.rsvg_handle_new_from_data(baseadr, length, error._error)
        my_error.raise_if_set()
        if rsvgobj != None :
            result = celf(rsvgobj)
        else :
            result = None
        #end if
        return \
            result
    #end new_from_data

    @classmethod
    def new_from_file(celf, file_name, error = None) :
        error, my_error = _get_error(error)
        result = rsvg.rsvg_handle_new_from_file(file_name.encode(), error._error)
        my_error.raise_if_set()
        if result == None :
            raise RuntimeError("rsvg_handle_new_from_file failed")
        #end if
        return \
            celf(result)
    #end new_from_file

    def write(self, data, error = None) :
        if isinstance(data, bytes) :
            baseadr = ct.cast(data, ct.c_void_p).value
            length = len(data)
        elif isinstance(data, bytearray) :
            baseadr = ct.addressof((ct.c_char * len(data)).from_buffer(data))
            length = len(data)
        elif isinstance(data, array.array) and data.typecode == "B" :
            baseadr, length = data.buffer_info()
        else :
            raise TypeError("data is not bytes, bytearray or array.array of bytes")
        #end if
        error, my_error = _get_error(error)
        success = rsvg.rsvg_handle_write(self._rsvgobj, baseadr, length, error._error)
        my_error.raise_if_set()
        return \
            success
    #end write

    def close(self, error = None) :
        error, my_error = _get_error(error)
        success = rsvg.rsvg_handle_close(self._rsvgobj, error._error)
        my_error.raise_if_set()
        return \
            success
    #end close

    def __del__(self) :
        if self._rsvgobj != None :
            rsvg.rsvg_handle_free(self._rsvgobj)
            self._rsvgobj = None
        #end if
    #end __del__

    @property
    def base_uri(self) :
        uri = rsvg.rsvg_handle_get_base_uri(self._rsvgobj)
        if uri != None :
            result = uri.decode()
        else :
            result = None
        #end if
        return \
            result
    #end base_uri

    @base_uri.setter
    def base_uri(self, uri) :
        rsvg.rsvg_handle_set_base_uri(self._rsvgobj, uri.encode())
    #end base_uri

    @property
    def title(self) :
        title = rsvg.rsvg_handle_get_title(self._rsvgobj)
        if title != None :
            result = title.decode()
        else :
            result = None
        #end if
        return \
            result
    #end title

    @property
    def desc(self) :
        desc = rsvg.rsvg_handle_get_desc(self._rsvgobj)
        if desc != None :
            result = desc.decode()
        else :
            result = None
        #end if
        return \
            result
    #end desc

    @property
    def metadata(self) :
        metadata = rsvg.rsvg_handle_get_metadata(self._rsvgobj)
        if metadata != None :
            result = metadata.decode()
        else :
            result = None
        #end if
        return \
            result
    #end metadata

    def set_dpi(self, dpi = 0) :
        if isinstance(dpi, Real) :
            rsvg.rsvg_handle_set_dpi(self._rsvgobj, dpi)
        elif isinstance(dpi, (Vector, tuple, list)) :
            dpi = Vector.from_tuple(dpi)
            rsvg.rsvg_handle_set_dpi_x_y(self._rsvgobj, dpi.x, dpi.y)
        else :
            raise TypeError("dpi must be a Real or a Vector")
        #end if
    #end set_dpi

    @property
    def dimensions(self) :
        dims = RSVG.DimensionData()
        rsvg.rsvg_handle_get_dimensions(self._rsvgobj, ct.byref(dims))
        return \
            Vector(dims.width, dims.height)
    #end dimensions

    def get_dimensions(self, id = None) :
        dims = RSVG.DimensionData()
        if id != None :
            success = rsvg.rsvg_handle_get_dimensions_sub(self._rsvgobj, ct.byref(dims), id.encode())
        else :
            rsvg.rsvg_handle_get_dimensions(self._rsvgobj, ct.byref(dims))
            success = True
        #end if
        if success :
            result = Vector(dims.width, dims.height)
        else :
            result = None
        #end if
        return \
            result
    #end get_dimensions
    get_dimensions_sub = get_dimensions # whichever name you prefer

    def get_position_sub(self, id) :
        pos = RSVG.PositionData()
        success = rsvg.rsvg_handle_get_position_sub(self._rsvgobj, ct.byref(pos))
        if success :
            result = Vector(pos.width, pos.height)
        else :
            result = None
        #end if
        return \
            result
    #end get_position_sub

    def has_sub(self, id) :
        return \
            rsvg.rsvg_handle_has_sub(self._rsvgobj, id.encode()) != 0
    #end has_sub

    def render_qahirah(self, ctx, id = None) :
        "renders the SVG image into a qahirah.Context. id is either None to render the" \
        " whole thing, or the name of the particular object to render."
        if not isinstance(ctx, qah.Context) :
            raise TypeError("ctx must be a qahirah.Context")
        #end if
        if id != None :
            success = rsvg.rsvg_handle_render_cairo_sub(self._rsvgobj, ctx._cairob, id.encode())
        else :
            success = rsvg.rsvg_handle_render_cairo.restype(self._rsvgobj, ctx._cairobj)
        #end if
        ctx._check() # hopefully will raise appropriate Cairo error here
        if not success :
            raise RuntimeError("render_cairo failed for some reason")
        #end if
    #end render_qahirah

#end Handle

def _atexit() :
    # disable all __del__ methods at process termination to avoid segfaults
    for cls in Error, Handle :
        delattr(cls, "__del__")
    #end for
#end _atexit
atexit.register(_atexit)
del _atexit
