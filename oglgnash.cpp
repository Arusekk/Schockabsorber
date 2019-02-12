#include <Python.h>
#include <opengl/Renderer_ogl.h>

// IDEA ABANDONED

// BEGIN stuff
namespace gnash {

struct BytesReader : public IOChannel
{
	std::string b;
	unsigned int pos;

	BytesReader(const std::string& by)
		:
		b(by),
		pos(0)
	{}

    std::streamsize read(void* dst, std::streamsize bytes) 
	{
		memcpy(dst, b.c_str()+pos, bytes);

		pos += bytes;
		return bytes;
	}

    std::streampos tell() const
	{
		return pos;
	}

    bool seek(std::streampos newPos)
	{
		pos=newPos;
		return true; 
	}
	
	
	// These here to satisfy the IOChannel interface requirements.
	// I wouldn't call them, if I were you.
	void go_to_end() { abort(); }

	bool eof() const { abort(); return false; }
    
	bool bad() const { return false; }

    size_t size() const { abort(); return -1; }
	
};

}

// END stuff

typedef struct {
    PyObject_HEAD,
    gnash::Renderer::External *ext;
    gnash::BytesReader *brd;
} oglgnash_CxxObject;

static PyTypeObject oglgnash_WidgetType = {
    PyVarObject_HEAD_INIT(NULL, 0)
    "oglgnash.Widget",             /* tp_name */
    sizeof(oglgnash_WidgetObject), /* tp_basicsize */
        0,                         /* tp_itemsize */
        widget_dealloc,            /* tp_dealloc */
        0,                         /* tp_print */
        0,                         /* tp_getattr */
        0,                         /* tp_setattr */
        0,                         /* tp_compare */
        0,                         /* tp_repr */
        0,                         /* tp_as_number */
        0,                         /* tp_as_sequence */
        0,                         /* tp_as_mapping */
        0,                         /* tp_hash */
        0,                         /* tp_call */
        0,                         /* tp_str */
        0,                         /* tp_getattro */
        0,                         /* tp_setattro */
        0,                         /* tp_as_buffer */
        Py_TPFLAGS_DEFAULT,        /* tp_flags */
        "Widgettt objects",        /* tp_doc */
};

static PyObject *
widget(PyObject *self, PyObject *args)
{
    const char *blob;
    size_t length;

    if (!PyArg_ParseTuple(args, "s#", &blob, &length))
        return NULL;

    gnash::BytesReader brd(std::string str(blob, length));

    gnash::Renderer *r = gnash::renderer::opengl::create_handler();

    boost:intrusive_ptr<gnash::movie_definition> movie = gnash::makeMovie(, runResources, );
//     gnash::Renderer::External(*r, gnash::rgba(0,0,0,0));

    return Py_BuildValue("i", 0);
}

static PyMethodDef OglgnashMethods[] = {
    {"widget", widget, METH_VARARGS, "Gives a widget that redraws itself xD"},
    {NULL, NULL, 0, NULL}
};

PyMODINIT_FUNC
initoglgnash()
{
    PyObject *m;
    m = Py_InitModule("oglgnash", OglgnashMethods);
    if (m == NULL)
        return;
    Py_INCREF(&oglgnash_WidgetType);
    PyModule_AddObject(m, "Widget", (PyObject *)&oglgnash_WidgetType);
}
