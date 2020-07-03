"""Pure-python wrapper for librsvg that has no dependencies on anything Gtk-related."""
#+
# Copyright 2017-2020 Lawrence D'Oliveiro <ldo@geek-central.gen.nz>.
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
    MINOR_VERSION = 48
    MICRO_VERSION = 7
    VERSION = "2.48.7"

    gboolean = ct.c_int
    guint = ct.c_uint
    gsize = ct.c_ulong
    GType = ct.c_uint

    Error = ct.c_uint
    ERROR_FAILED = 0

    HandleFlags = ct.c_uint
    HANDLE_FLAGS_NONE = 0
    HANDLE_FLAG_UNLIMITED = 1 << 0
    HANDLE_FLAG_KEEP_IMAGE_DATA = 1 << 1

    GQuark = ct.c_uint

    class GError(ct.Structure) :

        def __repr__(self) :
            return \
              (
                    "%s(domain = %d, code = %d, message = %s)"
                %
                    (type(self).__name__, self.domain, self.code, self.message)
              )
        #end __repr__

    #end GError
    GError._fields_ = \
        [
            ("domain", GQuark),
            ("code", ct.c_int),
            ("message", ct.c_char_p),
        ]
    GErrorPtr = ct.POINTER(GError)
    GErrorPtrPtr = ct.POINTER(GErrorPtr)

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

    class Rectangle(ct.Structure) :
        _fields_ = \
            [
                ("x", ct.c_double),
                ("y", ct.c_double),
                ("width", ct.c_double),
                ("height", ct.c_double),
            ]
    #end Rectangle
    RectanglePtr = ct.POINTER(Rectangle)

    Unit = ct.c_uint
    UNIT_PERCENT = 0
    UNIT_PX = 1
    UNIT_EM = 2
    UNIT_EX = 3
    UNIT_IN = 4
    UNIT_CM = 5
    UNIT_MM = 6
    UNIT_PT = 7
    UNIT_PC = 8

    class Length(ct.Structure) :
        pass
    #end Length
    Length._fields_ = \
        [
            ("length", ct.c_double),
            ("unit", Unit),
        ]

    DEFAULT_DPI = 90 # from rsvg-base.c

#end RSVG

#+
# Library globals
#-

if hasattr(rsvg, "librsvg_version") :
    librsvg_major_version = RSVG.guint.in_dll(rsvg, "librsvg_major_version")
    librsvg_minor_version = RSVG.guint.in_dll(rsvg, "librsvg_minor_version")
    librsvg_micro_version = RSVG.guint.in_dll(rsvg, "librsvg_micro_version")
    ibrsvg_version = ct.c_char_p.in_dll(rsvg, "librsvg_version")
#end if

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
rsvg.rsvg_handle_write.argtypes = (ct.c_void_p, ct.c_void_p, RSVG.gsize, RSVG.GErrorPtrPtr)
rsvg.rsvg_handle_close.restype = RSVG.gboolean
rsvg.rsvg_handle_close.argtypes = (ct.c_void_p, RSVG.GErrorPtrPtr)
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

rsvg.rsvg_handle_get_intrinsic_dimensions.restype = None
rsvg.rsvg_handle_get_intrinsic_dimensions.argtypes = (ct.c_void_p, ct.POINTER(RSVG.gboolean), ct.POINTER(RSVG.Length), ct.POINTER(RSVG.gboolean), ct.POINTER(RSVG.Length), ct.POINTER(RSVG.gboolean), ct.POINTER(RSVG.Rectangle))

rsvg.rsvg_handle_new_with_flags.restype = ct.c_void_p
rsvg.rsvg_handle_new_with_flags.argtypes = (RSVG.HandleFlags,)

rsvg.rsvg_handle_set_stylesheet.restype = RSVG.gboolean
rsvg.rsvg_handle_set_stylesheet.argtypes = (ct.c_void_p, ct.POINTER(ct.c_char), RSVG.gsize, RSVG.GErrorPtrPtr)

# GFile stuff NYI

rsvg.rsvg_handle_new_from_data.restype = ct.c_void_p
rsvg.rsvg_handle_new_from_data.argtypes = (ct.c_void_p, ct.c_ulong, RSVG.GErrorPtrPtr)
rsvg.rsvg_handle_new_from_file.restype = ct.c_void_p
rsvg.rsvg_handle_new_from_file.argtypes = (ct.c_char_p, RSVG.GErrorPtrPtr)

rsvg.rsvg_handle_free.restype = None
rsvg.rsvg_handle_free.argtypes = (ct.c_void_p,)
  # may be deprecated, but I don’t want to bring in any GLib/GObject dependencies

rsvg.rsvg_handle_render_cairo.restype = RSVG.gboolean
rsvg.rsvg_handle_render_cairo.argtypes = (ct.c_void_p, ct.c_void_p)
rsvg.rsvg_handle_render_cairo_sub.restype = RSVG.gboolean
rsvg.rsvg_handle_render_cairo_sub.argtypes = (ct.c_void_p, ct.c_void_p, ct.c_char_p)

rsvg.rsvg_handle_render_document.restype = RSVG.gboolean
rsvg.rsvg_handle_render_document.argtypes = (ct.c_void_p, ct.c_void_p, RSVG.RectanglePtr, RSVG.GErrorPtrPtr)
rsvg.rsvg_handle_get_geometry_for_layer.restype = RSVG.gboolean
rsvg.rsvg_handle_get_geometry_for_layer.argtypes = (ct.c_void_p, ct.c_char_p, RSVG.RectanglePtr, RSVG.RectanglePtr, RSVG.RectanglePtr, RSVG.GErrorPtrPtr)
rsvg.rsvg_handle_render_layer.restype = RSVG.gboolean
rsvg.rsvg_handle_render_layer.argtypes = (ct.c_void_p, ct.c_void_p, ct.c_char_p, RSVG.RectanglePtr, RSVG.GErrorPtrPtr)
rsvg.rsvg_handle_get_geometry_for_element.restype = RSVG.gboolean
rsvg.rsvg_handle_get_geometry_for_element.argtypes = (ct.c_void_p, ct.c_char_p, RSVG.RectanglePtr, RSVG.RectanglePtr, RSVG.GErrorPtrPtr)
rsvg.rsvg_handle_render_element.restype = RSVG.gboolean
rsvg.rsvg_handle_render_element.argtypes = (ct.c_void_p, ct.c_void_p, ct.c_char_p, RSVG.RectanglePtr, RSVG.GErrorPtrPtr)

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

# Note that I don’t currently provide any support for GError objects.
# In my (admittedly limited) experiments, it doesn’t look like librsvg
# returns anything meaningful in them anyway.
# Docs here <https://developer.gnome.org/glib/stable/glib-Error-Reporting.html>
# might be useful for figuring it out in future.

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
        elif isinstance(data, str) :
            data = data.encode() # to bytes
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
        rsvgobj = rsvg.rsvg_handle_new_from_data(baseadr, length, None)
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
        result = rsvg.rsvg_handle_new_from_file(file_name.encode(), None)
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
        elif isinstance(data, str) :
            data = data.encode() # to bytes
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
        success = rsvg.rsvg_handle_write(self._rsvgobj, baseadr, length, None)
        return \
            success
    #end write

    def close(self, error = None) :
        success = rsvg.rsvg_handle_close(self._rsvgobj, None)
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

    # TODO: get_intrinsic_dimensions

    def get_position_sub(self, id) :
        pos = RSVG.PositionData()
        success = rsvg.rsvg_handle_get_position_sub(self._rsvgobj, ct.byref(pos), id.encode())
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

    def render_cairo(self, ctx, id = None) :
        "renders the SVG image into a qahirah.Context. id is either None to render the" \
        " whole thing, or the name of the particular object to render."
        if not isinstance(ctx, qah.Context) :
            raise TypeError("ctx must be a qahirah.Context")
        #end if
        if id != None :
            success = rsvg.rsvg_handle_render_cairo_sub(self._rsvgobj, ctx._cairobj, id.encode())
        else :
            success = rsvg.rsvg_handle_render_cairo(self._rsvgobj, ctx._cairobj)
        #end if
        ctx._check() # hopefully will raise appropriate Cairo error here
        if not success :
            raise RuntimeError("render_cairo failed for some reason")
        #end if
    #end render_cairo

    # TODO: render_document, get_geometry_for_layer, render_layer,
    # get_geometry_for_element, render_element
    # once I figure out how to deal with GError args.

#end Handle

def _atexit() :
    # disable all __del__ methods at process termination to avoid segfaults
    for cls in Handle, :
        delattr(cls, "__del__")
    #end for
#end _atexit
atexit.register(_atexit)
del _atexit
