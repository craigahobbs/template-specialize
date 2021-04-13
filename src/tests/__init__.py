# Licensed under the MIT License
# https://github.com/craigahobbs/template-specialize/blob/main/LICENSE

import os
import tempfile
import unittest


class TestCase(unittest.TestCase):

    @staticmethod
    def create_test_files(file_defs):
        tempdir = tempfile.TemporaryDirectory()
        for path_parts, content in file_defs:
            if isinstance(path_parts, str):
                path_parts = [path_parts]
            path = os.path.join(tempdir.name, *path_parts)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w', encoding='utf-8') as file_:
                file_.write(content)
        return tempdir
