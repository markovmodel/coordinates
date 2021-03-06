import unittest

from chainsaw.data.util.fileformat_registry import FileFormatRegistry, FileFormatUnsupported
from chainsaw.data._base.datasource import DataSource


class TestFormatRegistry(unittest.TestCase):
    def test_multiple_calls_register(self):
        with self.assertRaises(RuntimeError) as exc:
            @FileFormatRegistry.register(".foo")
            @FileFormatRegistry.register(".bar")
            class test_src():
                pass
        self.assertIn("only once", exc.exception.args[0])

    def test_correct_reader_by_ext(self):

        @FileFormatRegistry.register(".foo")
        class test_src_foo(DataSource):
            pass

        @FileFormatRegistry.register(".bar")
        class test_src_bar(DataSource):
            pass

        self.assertEqual(FileFormatRegistry[".foo"], test_src_foo)
        self.assertEqual(FileFormatRegistry[".bar"], test_src_bar)

    def test_not_supported(self):
        ext = '.imsurethisisnotvalid'
        with self.assertRaises(FileFormatUnsupported) as exc:
            FileFormatRegistry[ext]
        self.assertIn(ext, exc.exception.args[0])
        self.assertIn('not supported', exc.exception.args[0])
