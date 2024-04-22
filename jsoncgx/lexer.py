#!/usr/bin/env python3

"""lexer.py: The JSONC lexer.

Functions:
  - lex(origin): Lex JSONC data.

Classes:
  - JSONCString: A string containing JSONC data
  - LexCeption: An exception type for lexing issues
  - Token and subclasses: Objects representing lexed tokens
  - TokenList: A collection of Tokens
"""

import re
from typing import Iterator

SPACE_RE=re.compile(r"[\x09\x0A\x0D\x20]+")

TOK_LEFT_SQUARE='['
TOK_RIGHT_SQUARE=']'
TOK_LEFT_CURLY='{'
TOK_RIGHT_CURLY='}'
TOK_COLON=':'
TOK_COMMA=','
TOK_TRUE="true"
TOK_FALSE="false"
TOK_NULL="null"

TOK_STRING_RE=re.compile(r'"(.*?[^\\])?"')
TOK_VALID_STRING_RE=re.compile(r"""
    "                  # opening double quote
    (
     [^\\"\x00-\x1F]   #  anything except backslash, double quote, or control
     |                 #  or
     \\["\\/bfnrt]     #  one of the 2-character escape sequences
     |                 #  or
     \\u[0-9A-Fa-f]{4} #  a 6-character unicode escape sequence
    )*?                # any amount but the minimum
    "                  # closing double quote
    """, re.X)
TOK_NUMBER_RE=re.compile(r"""
    -?
    (0|[1-9]\d*)
    (\.\d+)?
    ([eE][-+]?\d+)?
    """, re.X)

TOK_COMMENT_C_RE=re.compile(r"//[^\n]*\n")
TOK_COMMENT_CXX_RE=re.compile(r"/\*.*?\*/")


class JSONCString:
    """JSONCString: A string containing JSONC data.

    Attributes:
      - contents: str, the JSONC data

    Methods:
      - JSONCString[slice]: alias for JSONCString.contents[slice]
      - len(JSONCString): alias for len(JSONCString.contents)

      - postolinecolumn(pos): Convert a byte position in the contents to a
        line-column combo.
      - prettypos(pos): Get a description of the position of a byte.
    """
    # Private attributes:
    #   - _name: str, a description of the contents origin (file, stream, ...)
    #   - _newlines: list of int, the byte positions of the newline characters
    contents: str
    _name: str
    _newlines: list[int]

    def __init__(self, contents: str, name: str):
        """JSONCString(contents, name)

        Args:
          - contents: str, the JSONC data
          - name: str, a description of the contents origin (file, stream, ...)
        """
        self.contents = contents
        self._name = name
        self._newlines = list()
        pos = -1
        while True:
            pos = self.contents.find('\n', pos + 1)
            if pos == -1:
                break
            self._newlines.append(pos)

    def __getitem__(self, key: int | slice) -> str:
        return self.contents[key]

    def __len__(self) -> int:
        return len(self.contents)

    def postolinecolumn(self, pos: int) -> tuple[int, int]:
        """postolinecolumn(pos): Convert a byte position in the contents to a
        line-column combo.

        Args:
          - pos: int, the byte position, 0 based

        Return: tuple of (int, int), the line and column count, 1 based
        """
        if not self._newlines or pos <= self._newlines[0]:
            return (1, pos + 1)
        for i in range(1, len(self._newlines)):
            if self._newlines[i - 1] < pos <= self._newlines[i]:
                return (i + 1, pos - self._newlines[i - 1])
        return (len(self._newlines) + 1, pos - self._newlines[-1])

    def prettypos(self, pos: int) -> str:
        """prettypos(pos): Get a description of the position of a byte.

        Args:
          - pos: int, the byte position (0 based)

        Return: str, a prettyfied description of the position
        """
        pretty = self._name
        pretty += ": "
        if (not self._newlines
            or (len(self._newlines) == 1
                and len(self.contents) == self._newlines[0] + 1)):
            # one line
            pretty += f"byte {pos + 1}"
        else:
            line, column = self.postolinecolumn(pos)
            pretty += f"line {line}, column {column}"
        return pretty


class Token:
    """Token: Superclass for all token classes.

    Attributes:
      - origin: JSONCString, the JSONCString this token comes from
      - start: int, the byte position of the start of the token in origin
      - end: int, the byte position directly after the token in origin

    Methods:
      - repr(Token): Get a verbose representation of the token.
      - str(Token): Get the contents of the token.
    """
    origin: JSONCString
    start: int
    end: int

    def __init__(self, origin: JSONCString, start: int, end: int):
        """Token(origin, start, end)

        Args:
          - origin: JSONCString, the string this token comes from
          - start: int, the byte position of the start of the token in origin
          - end: int, the byte position directly after the token in origin
        """
        self.origin = origin
        self.start = start
        self.end = end

    def __repr__(self) -> str:
        line, column = self.origin.postolinecolumn(self.start)
        return f"[{type(self).__name__} '{str(self)}' {line}:{column}]"

    def __str__(self) -> str:
        return self.origin[self.start:self.end]


class TokenLeftSquare(Token): pass
class TokenRightSquare(Token): pass
class TokenLeftCurly(Token): pass
class TokenRightCurly(Token): pass
class TokenColon(Token): pass
class TokenComma(Token): pass
class TokenTrue(Token): pass
class TokenFalse(Token): pass
class TokenNull(Token): pass
class TokenString(Token): pass
class TokenNumber(Token): pass

class TokenComment(Token): pass
class TokenLineComment(TokenComment): pass
class TokenMultilineComment(TokenComment): pass


LITTERAL_TOKENS={
        TOK_LEFT_SQUARE: TokenLeftSquare,
        TOK_RIGHT_SQUARE: TokenRightSquare,
        TOK_LEFT_CURLY: TokenLeftCurly,
        TOK_RIGHT_CURLY: TokenRightCurly,
        TOK_COLON: TokenColon,
        TOK_COMMA: TokenComma,
        TOK_TRUE: TokenTrue,
        TOK_FALSE: TokenFalse,
        TOK_NULL: TokenNull
    }
REGEX_TOKENS={
        TOK_VALID_STRING_RE: TokenString,
        TOK_NUMBER_RE: TokenNumber,
        TOK_COMMENT_C_RE: TokenLineComment,
        TOK_COMMENT_CXX_RE: TokenMultilineComment
    }


class TokenList:
    """TokenList: A collection of tokens.

    Methods:
      - iter(TokenList): Get an iterator over the Tokens.

      - nocomments(): Get an iterator over the Tokens, excluding comment tokens.
    """
    # Private attributes:
    #   - _tokens: list of Token, the tokens
    _tokens: list[Token]

    def __init__(self, tokens: list[Token]):
        """TokenList(tokens)

        Args:
          - tokens: list of Token, the tokens to store
        """
        self._tokens = tokens

    def __iter__(self) -> Iterator[Token]:
        return iter(self._tokens)

    def nocomments(self) -> Iterator[Token]:
        """nocomments(): Get an iterator over the Tokens, excluding comment
        tokens.

        Return: iterator of Token
        """
        return filter(lambda t: not isinstance(t, TokenComment), self._tokens)


class LexCeption(Exception):
    """LexCeption: An exception type for lexing issues.

    Attributes:
      - args: tuple of (str,), the error message and location.
    """
    args: tuple[str]

    def __init__(self, origin: JSONCString, start: int, message: str):
        """LexCeption(origin, start, message)

        Args:
          - origin: JSONCString, the JSONCString where the lexing issue occurred
          - start: int, the byte position where the lexing issue occurred
          - message: str, the error message
        """
        super().__init__(f"{origin.prettypos(start)}: {message}")


def skipspace(origin: JSONCString, start: int =0) -> int:
    """skipspace(origin, start=0): Skip whitespace.

    Args:
      - origin: JSONCString, the contents to skip spaces in
      - start: int, optional (default: 0), the position in to skip from

    Return: int, the next position that is not a whitespace character
    """
    if match := SPACE_RE.match(origin.contents, start):
        return match.end()
    return start


def matchtoken(origin: JSONCString, start: int, tokens: list[Token]) -> int:
    """matchtoken(origin, start, tokens): Match a Token.

    Args:
      - origin: JSONCString, the contents to match in
      - start: int, the position to match at
      - tokens: list of Token, where to append the new Token to

    This function will attempt to match a Token, instanciate it, and append it
    to tokens.

    ⚠ This function modifies its argument ⚠

    Return: int, the position after the matched token

    Raise: LexCeption, if no token can be matched
    """
    for litteral, cls in LITTERAL_TOKENS.items():
        if origin.contents.startswith(litteral, start):
            end = start + len(litteral)
            tokens.append(cls(origin, start, end))
            return end

    for regex, cls in REGEX_TOKENS.items():
        if match := regex.match(origin.contents, start):
            end = match.end()
            tokens.append(cls(origin, start, end))
            return end

    if match := TOK_STRING_RE.match(origin.contents, start):
        raise LexCeption(origin, start, "invalid string litteral")

    raise LexCeption(origin, start, "unmatched token")


def lex(origin: JSONCString) -> TokenList:
    """lex(origin): Lex JSONC data.

    Args:
      - origin: JSONCString, the JSONC data

    Return: TokenList, the lexed tokens

    Raise: LexCeption, in case of lexing issues
    """
    start = skipspace(origin)
    tokens: list[Token] = list()

    start = skipspace(origin)
    while start < len(origin.contents):
        start = matchtoken(origin, start, tokens)
        start = skipspace(origin, start)

    return TokenList(tokens)


if __name__ == "__main__":
    import sys
    if len(sys.argv) == 1 or {"-h", "-help", "--help"} & set(sys.argv):
        print(f"Usage: {sys.argv[0]} <JSONC file>")
        exit(0)

    with open(sys.argv[1]) as f:
        origin = JSONCString(f.read(), sys.argv[1])
    try:
        tokenlist = lex(origin)
        for token in tokenlist:
            print(repr(token))
        exit(0)
    except LexCeption as e:
        print(*e.args)
        exit(1)
