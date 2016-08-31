
class FileFormatRegistry(object):
    """ Registry for trajectory file objects. """
    readers = {}

    @classmethod
    def register(cls, *args):
        """ register the given class as Reader class for given extension(s). """
        def decorator(f):
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


# TODO: should we use this or not? explicit is better than implicit, so only add the readers, we've tested?
# # if we have mdtraj loaded, use their file classes too.

#     FileFormatRegistry.readers.update(_reg.fileobjects)
