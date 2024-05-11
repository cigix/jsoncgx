import unittest

from jsoncgx import *

class SmokeTests(unittest.TestCase):
    def test_regular(self):
        loads("""{
  "value": 123.45e67,
  "array": [ null, true ]
}
""")
    def test_simple(self):
        loads("{}")
    def test_comment(self):
        loads("{/*123*/}")
    def test_empty(self):
        with self.assertRaises(Exception):
            loads("")
    def test_comment_only(self):
        with self.assertRaises(Exception):
            loads("/*123*/")

class ArrayDeleteTests(unittest.TestCase):
    def test_empty(self):
        editor = loads("[]")
        with self.assertRaises(Exception):
            editor.root.editdelete(0)
    def test_wrong_index(self):
        editor = loads("[1, 2, 3]")
        with self.assertRaises(Exception):
            editor.root.editdelete(3)
    def test_one_value(self):
        # [1]
        jsonc = "/*a*/[/*b*/1/*c*/]/*d*/"
        expected = "/*a*/[/*c*/]/*d*/"

        editor = loads(jsonc)
        editor.root.editdelete(0)
        self.assertEqual(editor.dumps(), expected)
    def test_beginning(self):
        # [1, 2]
        jsonc = "/*a*/[/*b*/1/*c*/,/*d*/2/*e*/]/*f*/"
        expected = "/*a*/[/*b*/2/*e*/]/*f*/"

        editor = loads(jsonc)
        editor.root.editdelete(0)
        self.assertEqual(editor.dumps(), expected)
    def test_end(self):
        # [1, 2]
        jsonc = "/*a*/[/*b*/1/*c*/,/*d*/2/*e*/]/*f*/"
        expected = "/*a*/[/*b*/1/*c*//*e*/]/*f*/"

        editor = loads(jsonc)
        editor.root.editdelete(-1)
        self.assertEqual(editor.dumps(), expected)
    def test_middle(self):
        # [1, 2, 3]
        jsonc = "/*a*/[/*b*/1/*c*/,/*d*/2/*e*/,/*f*/3/*g*/]/*h*/"
        expected = "/*a*/[/*b*/1/*c*/,/*d*/3/*g*/]/*h*/"

        editor = loads(jsonc)
        editor.root.editdelete(1)
        self.assertEqual(editor.dumps(), expected)

class ObjectDeleteTests(unittest.TestCase):
    def test_empty(self):
        editor = loads("{}")
        with self.assertRaises(Exception):
            editor.root.editdelete(0)
    def test_wrong_index(self):
        editor = loads('{"1":1,"2":2,"3":3}')
        with self.assertRaises(Exception):
            editor.root.editdelete(3)
    def test_one_value(self):
        # {"1":1}
        jsonc = '/*a*/{/*b*/"1"/*c*/:/*d*/1/*e*/}/*f*/'
        expected = "/*a*/{/*e*/}/*f*/"

        editor = loads(jsonc)
        editor.root.editdelete(0)
        self.assertEqual(editor.dumps(), expected)
    def test_beginning(self):
        # {"1": 1, "2": 2}
        jsonc = '/*a*/{/*b*/"1"/*c*/:/*d*/1/*e*/,/*f*/"2"/*g*/:/*h*/2/*i*/}/*j*/'
        expected = '/*a*/{/*b*/"2"/*g*/:/*h*/2/*i*/}/*j*/'

        editor = loads(jsonc)
        editor.root.editdelete(0)
        self.assertEqual(editor.dumps(), expected)
    def test_end(self):
        # {"1": 1, "2": 2}
        jsonc = '/*a*/{/*b*/"1"/*c*/:/*d*/1/*e*/,/*f*/"2"/*g*/:/*h*/2/*i*/}/*j*/'
        expected = '/*a*/{/*b*/"1"/*c*/:/*d*/1/*e*//*i*/}/*j*/'

        editor = loads(jsonc)
        editor.root.editdelete(-1)
        self.assertEqual(editor.dumps(), expected)
    def test_middle(self):
        # {"1": 1, "2": 2, "3": 3}
        jsonc = '/*a*/{/*b*/"1"/*c*/:/*d*/1/*e*/,/*f*/"2"/*g*/:/*h*/2/*i*/,/*j*/"3"/*k*/:/*l*/3/*m*/}/*n*/'
        expected = '/*a*/{/*b*/"1"/*c*/:/*d*/1/*e*/,/*f*/"3"/*k*/:/*l*/3/*m*/}/*n*/'

        editor = loads(jsonc)
        editor.root.editdelete(1)
        self.assertEqual(editor.dumps(), expected)

class ArrayInsertTests(unittest.TestCase):
    def test_empty(self):
        # []
        jsonc = "/*a*/[/*b*/]/*c*/"
        expected = "/*a*/[/*b*/1/*b*/]/*c*/"

        editor = loads(jsonc)
        editor.root.editinsert(0, 1)
        self.assertEqual(editor.dumps(), expected)
    def test_wrong_index(self):
        editor = loads("[1, 2, 3]")
        with self.assertRaises(Exception):
            editor.root.editinsert(5, 5)
    def test_beginning_one_value(self):
        # [2]
        jsonc = "/*a*/[/*b*/2/*c*/]/*d*/"
        expected = "/*a*/[/*b*/1,/*b*/2/*c*/]/*d*/"

        editor = loads(jsonc)
        editor.root.editinsert(0, 1)
        self.assertEqual(editor.dumps(), expected)
    def test_ending_one_value(self):
        # [1]
        jsonc = "/*a*/[/*b*/1/*c*/]/*d*/"
        expected = "/*a*/[/*b*/1,/*b*/2/*c*/]/*d*/"

        editor = loads(jsonc)
        editor.root.editinsert(1, 2)
        self.assertEqual(editor.dumps(), expected)
    def test_beginning(self):
        # [2, 3]
        jsonc = "/*a*/[/*b*/2/*c*/,/*d*/3/*e*/]/*f*/"
        expected = "/*a*/[/*b*/1,/*b*/2/*c*/,/*d*/3/*e*/]/*f*/"

        editor = loads(jsonc)
        editor.root.editinsert(0, 1)
        self.assertEqual(editor.dumps(), expected)
    def test_ending(self):
        # [1, 2]
        jsonc = "/*a*/[/*b*/1/*c*/,/*d*/2/*e*/]/*f*/"
        expected = "/*a*/[/*b*/1/*c*/,/*d*/2,/*d*/3/*e*/]/*f*/"

        editor = loads(jsonc)
        editor.root.editinsert(-1, 3)
        self.assertEqual(editor.dumps(), expected)
    def test_middle(self):
        # [1, 3]
        jsonc = "/*a*/[/*b*/1/*c*/,/*d*/3/*e*/]/*f*/"
        expected = "/*a*/[/*b*/1/*c*/,/*d*/2/*c*/,/*d*/3/*e*/]/*f*/"

        editor = loads(jsonc)
        editor.root.editinsert(1, 2)
        self.assertEqual(editor.dumps(), expected)
    def test_insert_array(self):
        # []
        jsonc = "[]"
        expected = "[[]]"

        editor = loads(jsonc)
        editor.root.editinsertnewarray(0)
        self.assertEqual(editor.dumps(), expected)
    def test_insert_object(self):
        # []
        jsonc = "[]"
        expected = "[{}]"

        editor = loads(jsonc)
        editor.root.editinsertnewobject(0)
        self.assertEqual(editor.dumps(), expected)

class ObjectInsertTests(unittest.TestCase):
    def test_empty(self):
        # {}
        jsonc = "/*a*/{/*b*/}/*c*/"
        expected = '/*a*/{/*b*/"1":1/*b*/}/*c*/'

        editor = loads(jsonc)
        editor.root.editinsert(0, "1", 1)
        self.assertEqual(editor.dumps(), expected)
    def test_wrong_index(self):
        editor = loads('{"1": 1, "2": 2, "3": 3}')
        with self.assertRaises(Exception):
            editor.root.editinsert(5, "5", 5)
    def test_beginning_one_value(self):
        # {"2": 2}
        jsonc = '/*a*/{/*b*/"2"/*c*/:/*d*/2/*e*/}/*f*/'
        expected = '/*a*/{/*b*/"1"/*c*/:/*d*/1,/*b*/"2"/*c*/:/*d*/2/*e*/}/*f*/'

        editor = loads(jsonc)
        editor.root.editinsert(0, "1", 1)
        self.assertEqual(editor.dumps(), expected)
    def test_ending_one_value(self):
        # {"1": 1}
        jsonc = '/*a*/{/*b*/"1"/*c*/:/*d*/1/*e*/}/*f*/'
        expected = '/*a*/{/*b*/"1"/*c*/:/*d*/1,/*b*/"2"/*c*/:/*d*/2/*e*/}/*f*/'

        editor = loads(jsonc)
        editor.root.editinsert(1, "2", 2)
        self.assertEqual(editor.dumps(), expected)
    def test_beginning(self):
        # {"2": 2, "3": 3}
        jsonc = '/*a*/{/*b*/"2"/*c*/:/*d*/2/*e*/,/*f*/"3"/*g*/:/*h*/3/*i*/}/*j*/'
        expected = '/*a*/{/*b*/"1"/*c*/:/*d*/1,/*b*/"2"/*c*/:/*d*/2/*e*/,/*f*/"3"/*g*/:/*h*/3/*i*/}/*j*/'

        editor = loads(jsonc)
        editor.root.editinsert(0, "1", 1)
        self.assertEqual(editor.dumps(), expected)
    def test_ending(self):
        # {"1": 1, "2": 2}
        jsonc = '/*a*/{/*b*/"1"/*c*/:/*d*/1/*e*/,/*f*/"2"/*g*/:/*h*/2/*i*/}/*j*/'
        expected = '/*a*/{/*b*/"1"/*c*/:/*d*/1/*e*/,/*f*/"2"/*g*/:/*h*/2,/*f*/"3"/*g*/:/*h*/3/*i*/}/*j*/'

        editor = loads(jsonc)
        editor.root.editinsert(-1, "3", 3)
        self.assertEqual(editor.dumps(), expected)
    def test_middle(self):
        # {"1": 1, "3": 3}
        jsonc = '/*a*/{/*b*/"1"/*c*/:/*d*/1/*e*/,/*f*/"3"/*h*/:/*i*/3/*j*/}/*k*/'
        expected = '/*a*/{/*b*/"1"/*c*/:/*d*/1/*e*/,/*f*/"2"/*c*/:/*d*/2/*e*/,/*f*/"3"/*h*/:/*i*/3/*j*/}/*k*/'

        editor = loads(jsonc)
        editor.root.editinsert(1, "2", 2)
        self.assertEqual(editor.dumps(), expected)
    def test_insert_array(self):
        # {}
        jsonc = "{}"
        expected = '{"1":[]}'

        editor = loads(jsonc)
        editor.root.editinsertnewarray(0, "1")
        self.assertEqual(editor.dumps(), expected)
    def test_insert_object(self):
        # {}
        jsonc = "{}"
        expected = '{"1":{}}'

        editor = loads(jsonc)
        editor.root.editinsertnewobject(0, "1")
        self.assertEqual(editor.dumps(), expected)

class ReplaceTests(unittest.TestCase):
    def test_array_value(self):
        # [1, 42, 3]
        jsonc = "[1, 42, 3]"
        expected = "[1, 2, 3]"

        editor = loads(jsonc)
        editor.root.editreplace(1, 2)
        self.assertEqual(editor.dumps(), expected)
    def test_array_array(self):
        # [1, 42, 3]
        jsonc = "[1, 42, 3]"
        expected = "[1, [], 3]"

        editor = loads(jsonc)
        editor.root.editreplacenewarray(1)
        self.assertEqual(editor.dumps(), expected)
    def test_array_object(self):
        # [1, 42, 3]
        jsonc = "[1, 42, 3]"
        expected = "[1, {}, 3]"

        editor = loads(jsonc)
        editor.root.editreplacenewobject(1)
        self.assertEqual(editor.dumps(), expected)
    def test_object_name(self):
        # {"1": 1, "42": 2, "3": 3}
        jsonc = '{"1": 1, "42": 2, "3": 3}'
        expected = '{"1": 1, "2": 2, "3": 3}'

        editor = loads(jsonc)
        editor.root.editreplacename(1, "2")
        self.assertEqual(editor.dumps(), expected)
    def test_object_value(self):
        # {"1": 1, "2": 42, "3": 3}
        jsonc = '{"1": 1, "2": 42, "3": 3}'
        expected = '{"1": 1, "2": 2, "3": 3}'

        editor = loads(jsonc)
        editor.root.editreplacevalue(1, 2)
        self.assertEqual(editor.dumps(), expected)
    def test_object_array(self):
        # {"1": 1, "2": 2, "3": 3}
        jsonc = '{"1": 1, "2": 2, "3": 3}'
        expected = '{"1": 1, "2": [], "3": 3}'

        editor = loads(jsonc)
        editor.root.editreplacenewarray(1)
        self.assertEqual(editor.dumps(), expected)
    def test_object_object(self):
        # {"1": 1, "2": 2, "3": 3}
        jsonc = '{"1": 1, "2": 2, "3": 3}'
        expected = '{"1": 1, "2": {}, "3": 3}'

        editor = loads(jsonc)
        editor.root.editreplacenewobject(1)
        self.assertEqual(editor.dumps(), expected)

if __name__ == "__main__":
    unittest.main()
