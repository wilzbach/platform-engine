import re

from requests.structures import CaseInsensitiveDict

from ..Exceptions import StoryscriptRuntimeError
from ..Types import (
    InternalCommand,
    InternalService,
    SafeInternalCommand,
    SafeStreamingService,
    StreamingService,
)
from ..entities.Multipart import FileFormField, FormField


class TypeUtils:

    RE_PATTERN = type(re.compile("a"))

    allowed_types = [
        FileFormField,
        FormField,
        RE_PATTERN,
        str,
        int,
        float,
        bool,
        list,
        dict,
        bytes,
    ]

    @staticmethod
    def isnamedtuple(o):
        t = type(o)
        b = t.__bases__
        if len(b) != 1 or b[0] != tuple:
            return False
        f = getattr(t, "_fields", None)
        if not isinstance(f, tuple):
            return False
        return all(type(n) == str for n in f)

    @staticmethod
    def safe_type(o):
        """
        This will safely convert the object to a safe type that won't
        expose sensitive information or internal data.

        :param o: the object you wish to convert
        :return: returns a converted type
        """
        if o is None:
            return None

        if isinstance(o, dict) or isinstance(o, CaseInsensitiveDict):
            _dict = {}
            for key, val in o.items():
                _dict[key] = TypeUtils.safe_type(val)

            return _dict
        elif isinstance(o, list):

            def build_list():
                for d in o:
                    yield TypeUtils.safe_type(d)

            return list(build_list())
        elif isinstance(o, StreamingService):
            return SafeStreamingService(name=o.name, command=o.command)
        elif isinstance(o, InternalService):
            service = InternalService(commands={})
            for key, value in o.commands.items():
                service.commands[key] = TypeUtils.safe_type(value)
            return service
        elif isinstance(o, InternalCommand):
            return SafeInternalCommand(
                arguments=o.arguments, output_type=o.output_type
            )
        else:
            # ensure the type is a primitive type
            if not type(o) in TypeUtils.allowed_types:
                raise StoryscriptRuntimeError(
                    message=f"Incompatible type: " f"{type(o)}"
                )

            return o
