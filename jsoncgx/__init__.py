"""jsoncgx: An overpowered JSON-with-comments parser with inplace edition.

Functions:
  - load(fp, name): Parse a JSONC file.
  - loadf(path): Parse a JSONC file.
  - loads(s): Parse a JSONC string.

Re-exported classes:
  - lexer.JSONCString: A string containing JSONC data
  - lexer.LexCeption: An exception type for lexing issues
  - parser.ParseXception: An exception type for parsing issues
  - rexel.JSONNumber, JSONString, JSONBool, JSONNull: JSON values
  - rexel.JSONArray, JSONObject, JSONEditor: Editable JSON containers

Re-exported functions:
  - abstract.abstract(cst): Turn a CST into an AST.
  - lexer.lex(origin): Lex JSONC data.
  - parser.parse(tokens): Parse a list of tokens into a CST.
"""

from os import PathLike
from typing import TYPE_CHECKING, IO, Optional

try:
    from .lexer import JSONCString, lex, LexCeption
    from .parser import parse, ParseXception
    from .abstract import abstract
    from .rexel import (JSONNumber, JSONString, JSONBool, JSONNull, JSONArray,
                        JSONObject, JSONEditor)
except ImportError:
    if not TYPE_CHECKING:
        from lexer import JSONCString, lex, LexCeption
        from parser import parse, ParseXception
        from abstract import abstract
        from rexel import (JSONNumber, JSONString, JSONBool, JSONNull,
                           JSONArray, JSONObject, JSONEditor)

def loads(s: str | bytes, name: Optional[str] =None,
          allow_comments: Optional[bool] =True) -> JSONEditor:
    """loads(s, name=None, allow_comments=True): Parse a JSONC string.

    Args:
      - s: str or bytes, the JSONC contents to parse
      - name: str, optional, the filename shown in case of error
      - allow_comments: bool, optional (default: True), should comments be
        removed before parsing

    Return: JSONEditor, the editable JSONC AST.

    Raise:
      - LexCeption: in case of lexing issue (unmatched token)
      - ParseXception: in case of parsing issue (comments, syntax errors)

    The parser always rejects comments: with allow_comments, comments are
    filtered out before the parsing phase.
    """
    if not name:
        name = "<string>"
    origin = JSONCString(str(s), name)
    tokenlist = lex(origin)
    if allow_comments:
        cst = parse(tokenlist.nocomments())
    else:
        cst = parse(tokenlist)
    ast = abstract(cst)
    return JSONEditor.fromAST(ast)

def load(fp: IO[str], name: str, allow_comments: Optional[bool] =True
         )-> JSONEditor:
    """load(fp, name, allow_comments=True): Parse a JSONC file.

    Args:
      - fp: a .read() supporting object, the JSONC source
      - name: str, the filename shown in case of error
      - allow_comments: bool, optional (default: True), should comments be
        removed before parsing

    Alias for:
      loads(fp.read(), name, allow_comments)
    """
    return loads(fp.read(), name, allow_comments)

def loadf(path: PathLike, allow_comments: Optional[bool] =True) -> JSONEditor:
    """loadf(path, allow_comments=True): Parse a JSONC file.

    Args:
      - path: path-like object, the file to parse
      - allow_comments: bool, optional (default: True), should comments be
        removed before parsing

    Alias for:
      with open(path, "r") as f:
          loads(f.read(), path, allow_comments)
    """
    with open(path, "r") as f:
        return loads(f.read(), str(path), allow_comments)
