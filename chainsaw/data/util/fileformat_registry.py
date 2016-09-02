
class FileFormatRegistry(object):
    """ Registry for trajectory file objects. """
    readers = {}

    @classmethod
    def register(cls, *args):
        """ register the given class as Reader class for given extension(s). """
        def decorator(f):
            if hasattr(f, 'SUPPORTED_EXTENSIONS') and f.SUPPORTED_EXTENSIONS is not ():
                raise RuntimeError("please call register() only once per class!")
            extensions = tuple(args)
            cls.readers.update({e: f for e in extensions})
            f.SUPPORTED_EXTENSIONS = extensions
            return f
        return decorator

    @staticmethod
    def is_md_format(extension):
        from chainsaw.data import FeatureReader
        return extension in FeatureReader.SUPPORTED_EXTENSIONS

# singleton pattern
FileFormatRegistry = FileFormatRegistry()
