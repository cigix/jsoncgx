#!/usr/bin/env python3

"""parser.py: The JSON parser.

Functions:
  - parse(tokens): Parse a list of tokens into a CST.

Classes:
  - CNode and subclasses: Nodes in the CST
  - CST: A Concrete Syntax Tree
  - ParseXception: An exception type for parsing issues
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Iterable, Optional

try:
    from .lexer import (Token, TokenLeftSquare, TokenRightSquare,
                        TokenLeftCurly, TokenRightCurly, TokenColon, TokenComma,
                        TokenTrue, TokenFalse, TokenNull, TokenString,
                        TokenNumber, TokenComment)
except ImportError:
    if not TYPE_CHECKING:
        from lexer import (Token, TokenLeftSquare, TokenRightSquare,
                           TokenLeftCurly, TokenRightCurly, TokenColon,
                           TokenComma, TokenTrue, TokenFalse, TokenNull,
                           TokenString, TokenNumber, TokenComment)


class ParseXception(Exception):
    """ParseXception: An exception type for parsing issues.

    Attributes:
      - args: list of string of length 1, the error message and location.
    """
    def __init__(self, token: Token, message: str):
        """ParseXception(token, message)

        Args:
          - token: Token, the Token where the parsing issue occurred
          - message: str, the error message
        """
        super().__init__(f"{token.origin.prettypos(token.start)}: {message}")


class CNode:
    """CNode: A node in the CST.

    Methods:
      - repr(CNode): a string of the type of the node

      - start(): Get the first token of the subtree.
      - end(): Get the last token of the subtree.
      - tographviz(): Get a Graphviz representation of the subtree.
    """
    def __repr__(self) -> str:
        return type(self).__name__

    def start(_) -> Token:
        """start(): Get the first token of the subtree.

        Return: Token, the first token of the subtree
        """
        raise NotImplementedError()

    def end(_) -> Token:
        """end(): Get the last token of the subtree.

        Return: Token, the last token of the subtree
        """
        raise NotImplementedError()

    def tographviz(_) -> str:
        """tographviz(): Get a Graphviz representation of the subtree.

        Return: str, a Graphviz representation of the subtree
        """
        raise NotImplementedError()


class CNodeToken(CNode):
    """CNodeToken: A CST node for a token."""
    # Private attributes:
    #   - _token: Token, the token associated with this node
    _token: Token

    def __init__(self, token: Token):
        """CNodeToken(token)

        Args:
          - token: Token, the token associated with this node
        """
        self._token = token

    def start(self) -> Token:
        return self._token

    def end(self) -> Token:
        return self._token

    def tographviz(self) -> str:
        return f'  "{id(self)}" [label=<"{str(self._token)}"> shape=box];\n'


class CNodeLeftSquare(CNodeToken): pass
class CNodeRightSquare(CNodeToken): pass
class CNodeLeftCurly(CNodeToken): pass
class CNodeRightCurly(CNodeToken): pass
class CNodeColon(CNodeToken): pass
class CNodeComma(CNodeToken): pass
class CNodeTrue(CNodeToken): pass
class CNodeFalse(CNodeToken): pass
class CNodeNull(CNodeToken): pass
class CNodeString(CNodeToken): pass
class CNodeNumber(CNodeToken): pass


class CNodeValue(CNode):
    """CNodeValue: A CST node for a JSON value."""
    pass


class CNodeNumberValue(CNodeValue):
    """CNodeNumberValue: A CST node for a JSON number.

    Attributes:
      - number: CNodeNumber, the number token node
    """
    number: CNodeNumber

    def __init__(self, child: CNodeNumber):
        """CNodeNumberValue(child)

        Args:
          - child: CNodeNumber, the number token node
        """
        self.number = child

    def start(self) -> Token:
        return self.number.start()

    def end(self) -> Token:
        return self.number.end()

    def tographviz(self) -> str:
        graphviz = f'  "{id(self)}" [label="Number"];\n'
        graphviz += self.number.tographviz()
        graphviz += f'  "{id(self)}" -> "{id(self.number)}";\n'
        return graphviz


class CNodeStringValue(CNodeValue):
    """CNodeStringValue: A CST node for a JSON string.

    Attributes:
      - string: CNodeString, the string token node
    """
    string: CNodeString

    def __init__(self, child: CNodeString):
        """CNodeStringValue(child)

        Args:
          - child: CNodeString, the string token node
        """
        self.string = child

    def start(self) -> Token:
        return self.string.start()

    def end(self) -> Token:
        return self.string.end()

    def tographviz(self) -> str:
        graphviz = f'  "{id(self)}" [label="String"];\n'
        graphviz += self.string.tographviz()
        graphviz += f'  "{id(self)}" -> "{id(self.string)}";\n'
        return graphviz


class CNodeBoolValue(CNodeValue):
    """CNodeBoolValue: A CST node for a JSON boolean.

    Attributes:
      - value: CNodeTrue or CNodeFalse, the boolean token node
    """
    value: CNodeTrue | CNodeFalse

    def __init__(self, child: CNodeTrue | CNodeFalse):
        """CNodeBoolValue(child)

        Args:
          - child: CNodeTrue or CNodeFalse, the boolean token node
        """
        self.value = child

    def start(self) -> Token:
        return self.value.start()

    def end(self) -> Token:
        return self.value.end()

    def tographviz(self) -> str:
        graphviz = f'  "{id(self)}" [label="Boolean"];\n'
        graphviz += self.value.tographviz()
        graphviz += f'  "{id(self)}" -> "{id(self.value)}";\n'
        return graphviz


class CNodeNullValue(CNodeValue):
    """CNodeNullValue: A CST node for a JSON null.

    Attributes:
      - value: CNodeNull, the null token node
    """
    value: CNodeNull

    def __init__(self, child: CNodeNull):
        """CNodeNullValue(child)

        Args:
          - child: CNodeNull, the null token node
        """
        self.value = child

    def start(self) -> Token:
        return self.value.start()

    def end(self) -> Token:
        return self.value.end()

    def tographviz(self) -> str:
        graphviz = f'  "{id(self)}" [label="Null"];\n'
        graphviz += self.value.tographviz()
        graphviz += f'  "{id(self)}" -> "{id(self.value)}";\n'
        return graphviz


class CNodeArrayList(CNode):
    """CNodeArrayList: A CST node for the list of values in a JSON array.

    Attributes:
      - left: CNodeArrayList, the left hand sublist node
      - comma: CNodeComma, the comma token node
      - right: CNodeValue, the right hand value node
    """
    left: CNodeArrayList
    comma: CNodeComma
    right: CNodeValue

    def __init__(self, left: CNodeArrayList, comma: CNodeComma,
                 right: CNodeValue):
        """CNodeArrayList(left, comma, right)

        Args:
          - left: CNodeArrayList, the left hand sublist node
          - comma: CNodeComma, the comma token node
          - right: CNodeValue, the right hand value node
        """
        self.left = left
        self.comma = comma
        self.right = right

    def start(self) -> Token:
        return self.left.start()

    def end(self) -> Token:
        return self.right.end()

    def tographviz(self) -> str:
        graphviz = f'  "{id(self)}" [label="ArrayList"];\n'
        graphviz += self.left.tographviz()
        graphviz += f'  "{id(self)}" -> "{id(self.left)}";\n'
        graphviz += self.comma.tographviz()
        graphviz += f'  "{id(self)}" -> "{id(self.comma)}";\n'
        graphviz += self.right.tographviz()
        graphviz += f'  "{id(self)}" -> "{id(self.right)}";\n'
        return graphviz


class CNodeArrayListStart(CNodeArrayList):
    """CNodeArrayListStart: A CST node for the start of a list of values in a
    JSON array.

    Attributes:
      - value: CNodeValue, the first value node
    """
    value: CNodeValue

    def __init__(self, child: CNodeValue):
        """CNodeArrayListStart(child)

        Args:
          - child: CNodeValue, the first value node
        """
        self.value = child

    def start(self) -> Token:
        return self.value.start()

    def end(self) -> Token:
        return self.value.end()

    def tographviz(self) -> str:
        graphviz = f'  "{id(self)}" [label="ArrayListStart"];\n'
        graphviz += self.value.tographviz()
        graphviz += f'  "{id(self)}" -> "{id(self.value)}";\n'
        return graphviz


class CNodeArray(CNodeValue):
    """CNodeArray: A CST node for a JSON array.

    Attributes:
      - leftbracket: CNodeLeftSquare, the opening bracket token node
      - rightbracket: CNodeRightSquare, the closing bracket token node
      - values: CNodeArrayList or None, the list of value nodes
    """
    leftbracket: CNodeLeftSquare
    rightbracket: CNodeRightSquare
    values: Optional[CNodeArrayList]

    def __init__(self, leftbracket: CNodeLeftSquare,
                 rightbracket: CNodeRightSquare,
                 values: Optional[CNodeArrayList] =None):
        """CNodeArray(leftbracket, rightbracket, values=None)

        Args:
          - leftbracket: CNodeLeftSquare, the opening bracket token node
          - rightbracket: CNodeRightSquare, the closing bracket token node
          - values: CNodeArrayList, optional, the list of value nodes
        """
        self.leftbracket = leftbracket
        self.rightbracket = rightbracket
        self.values = values

    def start(self) -> Token:
        return self.leftbracket.start()

    def end(self) -> Token:
        return self.rightbracket.end()

    def tographviz(self) -> str:
        graphviz = f'  "{id(self)}" [label="Array"];\n'
        graphviz += self.leftbracket.tographviz()
        graphviz += f'  "{id(self)}" -> "{id(self.leftbracket)}";\n'
        if self.values:
            graphviz += self.values.tographviz()
            graphviz += f'  "{id(self)}" -> "{id(self.values)}";\n'
        graphviz += self.rightbracket.tographviz()
        graphviz += f'  "{id(self)}" -> "{id(self.rightbracket)}";\n'
        return graphviz


class CNodeNameValue(CNode):
    """CNodeNameValue: A CST node for a name:value pair.

    Attributes:
      - name: CNodeStringValue, the name string token node
      - colon: CNodeColon, the colon token node
      - value: CNodeValue, the value node
    """
    name: CNodeStringValue
    colon: CNodeColon
    value: CNodeValue

    def __init__(self, name: CNodeStringValue, colon: CNodeColon,
                 value: CNodeValue):
        self.name = name
        self.colon = colon
        self.value = value

    def start(self) -> Token:
        return self.name.start()

    def end(self) -> Token:
        return self.value.end()

    def tographviz(self) -> str:
        graphviz = f'  "{id(self)}" [label="NameValue"];\n'
        graphviz += self.name.tographviz()
        graphviz += f'  "{id(self)}" -> "{id(self.name)}";\n'
        graphviz += self.colon.tographviz()
        graphviz += f'  "{id(self)}" -> "{id(self.colon)}";\n'
        graphviz += self.value.tographviz()
        graphviz += f'  "{id(self)}" -> "{id(self.value)}";\n'
        return graphviz


class CNodeObjectList(CNode):
    """CNodeObjectList: A CST node for the list of name:value pairs in a JSON
    object.

    Attributes:
      - left: CNodeObjectList, the left hand sublist node
      - comma: CNodeComma, the comma token node
      - right: CNodeNameValue, the right hand name:value pair node
    """
    left: CNodeObjectList
    comma: CNodeComma
    right: CNodeNameValue

    def __init__(self, left: CNodeObjectList, comma: CNodeComma,
                 right: CNodeNameValue):
        """CNodeObjectList(left, comma, right)

        Args:
          - left: CNodeObjectList, the left hand sublist node
          - comma: CNodeComma, the comma token node
          - right: CNodeNameValue, the right hand name:value pair node
        """
        self.left = left
        self.comma = comma
        self.right = right

    def start(self) -> Token:
        return self.left.start()

    def end(self) -> Token:
        return self.right.end()

    def tographviz(self) -> str:
        graphviz = f'  "{id(self)}" [label="ObjectList"];\n'
        graphviz += self.left.tographviz()
        graphviz += f'  "{id(self)}" -> "{id(self.left)}";\n'
        graphviz += self.comma.tographviz()
        graphviz += f'  "{id(self)}" -> "{id(self.comma)}";\n'
        graphviz += self.right.tographviz()
        graphviz += f'  "{id(self)}" -> "{id(self.right)}";\n'
        return graphviz


class CNodeObjectListStart(CNodeObjectList):
    """CNodeObjectListStart: A CST node for the start of a list of node:value
    pairs in a JSON object.

    Attributes:
      - namevalue: CNodeNameValue, the first name:value pair node
    """
    namevalue: CNodeNameValue

    def __init__(self, child: CNodeNameValue):
        """CNodeObjectListStart(child)

        Args:
          - child: CNodeNameValue, the first name:value pair node
        """
        self.value = child

    def start(self) -> Token:
        return self.value.start()

    def end(self) -> Token:
        return self.value.end()

    def tographviz(self) -> str:
        graphviz = f'  "{id(self)}" [label="ObjectListStart"];\n'
        graphviz += self.value.tographviz()
        graphviz += f'  "{id(self)}" -> "{id(self.value)}";\n'
        return graphviz


class CNodeObject(CNodeValue):
    """CNodeObject: A CST node for a JSON object.

    Attributes:
      - leftbracket: CNodeLeftCurly, the opening bracket token node
      - rightbracket: CNodeRightCurly, the closing bracket token node
      - items: CNodeObjectList or None, the list of name:value pair nodes
    """
    leftbracket: CNodeLeftCurly
    rightbracket: CNodeRightCurly
    items: Optional[CNodeObjectList]

    def __init__(self, leftbracket: CNodeLeftCurly,
                 rightbracket: CNodeRightCurly,
                 items: Optional[CNodeObjectList] =None):
        """CNodeArray(leftbracket, rightbracket, items=None)

        Args:
          - leftbracket: CNodeLeftCurly, the opening bracket token node
          - rightbracket: CNodeRightCurly, the closing bracket token node
          - items: CNodeObjectList, optional, the list of value nodes
        """
        self.leftbracket = leftbracket
        self.rightbracket = rightbracket
        self.items = items

    def start(self) -> Token:
        return self.leftbracket.start()

    def end(self) -> Token:
        return self.rightbracket.end()

    def tographviz(self) -> str:
        graphviz = f'  "{id(self)}" [label="Object"];\n'
        graphviz += self.leftbracket.tographviz()
        graphviz += f'  "{id(self)}" -> "{id(self.leftbracket)}";\n'
        if self.items:
            graphviz += self.items.tographviz()
            graphviz += f'  "{id(self)}" -> "{id(self.items)}";\n'
        graphviz += self.rightbracket.tographviz()
        graphviz += f'  "{id(self)}" -> "{id(self.rightbracket)}";\n'
        return graphviz


def shift(tokens: list[Token]) -> CNode:
    """shift(tokens): Shift a token to a CNode.

    Args:
      - tokens: list of Token, the token list

    Return: CNode, the new node.

    ⚠️ This function modifies its argument ⚠️
    """
    token = tokens.pop(0)
    match token:
        case TokenLeftSquare():
            return CNodeLeftSquare(token)
        case TokenRightSquare():
            return CNodeRightSquare(token)
        case TokenLeftCurly():
            return CNodeLeftCurly(token)
        case TokenRightCurly():
            return CNodeRightCurly(token)
        case TokenColon():
            return CNodeColon(token)
        case TokenComma():
            return CNodeComma(token)
        case TokenTrue():
            return CNodeTrue(token)
        case TokenFalse():
            return CNodeFalse(token)
        case TokenNull():
            return CNodeNull(token)
        case TokenString():
            return CNodeString(token)
        case TokenNumber():
            return CNodeNumber(token)
        case TokenComment():
            raise ParseXception(token, "Cannot parse comment")
        case _:
            raise ParseXception(token,
                                f"Unknown token type: {type(token).__name__}")


def reduce(stack: list[CNode]) -> bool:
    """reduce(stack): Reduce the CNode stack maybe.

    Args:
      - stack: list of CNode, the node stack

    Return: bool, whether the stack was reduced or not.

    ⚠️ This function modifies its argument ⚠️
    """
    if not stack:
        return False # shift

    if isinstance(stack[-1], CNodeLeftSquare):
        return False # shift
    if isinstance(stack[-1], CNodeRightSquare):
        if 2 <= len(stack) and isinstance(stack[-2], CNodeLeftSquare):
            # reduce
            stack[-2:] = [CNodeArray(*stack[-2:])] # type: ignore
            return True
        if (3 <= len(stack)
            and isinstance(stack[-3], CNodeLeftSquare)
            and isinstance(stack[-2], CNodeArrayList)):
            # reduce
            stack[-3:] = [CNodeArray(stack[-3], stack[-1], stack[-2])]
            return True
        raise ParseXception(stack[-1].start(), "Unmatched closing bracket")
    if isinstance(stack[-1], CNodeLeftCurly):
        return False # shift
    if isinstance(stack[-1], CNodeRightCurly):
        if 2 <= len(stack) and isinstance(stack[-2], CNodeLeftCurly):
            # reduce
            stack[-2:] = [CNodeObject(*stack[-2:])] # type: ignore
            return True
        if (3 <= len(stack)
            and isinstance(stack[-3], CNodeLeftCurly)
            and isinstance(stack[-2], CNodeObjectList)):
            # reduce
            stack[-3:] = [CNodeObject(stack[-3], stack[-1], stack[-2])]
            return True
        raise ParseXception(stack[-1].start(), "Unmatched closing bracket")
    if isinstance(stack[-1], CNodeColon):
        return False # shift
    if isinstance(stack[-1], CNodeComma):
        return False # shift
    if isinstance(stack[-1], CNodeTrue):
        # reduce
        stack[-1:] = [CNodeBoolValue(stack[-1])]
        return True
    if isinstance(stack[-1], CNodeFalse):
        # reduce
        stack[-1:] = [CNodeBoolValue(stack[-1])]
        return True
    if isinstance(stack[-1], CNodeNull):
        # reduce
        stack[-1:] = [CNodeNullValue(stack[-1])]
        return True
    if isinstance(stack[-1], CNodeString):
        # reduce
        stack[-1:] = [CNodeStringValue(stack[-1])]
        return True
    if isinstance(stack[-1], CNodeNumber):
        # reduce
        stack[-1:] = [CNodeNumberValue(stack[-1])]
        return True
    if isinstance(stack[-1], CNodeValue):
        if 2 <= len(stack) and isinstance(stack[-2], CNodeLeftSquare):
            # reduce
            stack[-1:] = [CNodeArrayListStart(stack[-1])]
            return True
        if (2 <= len(stack)
            and isinstance(stack[-2], CNodeLeftCurly)
            and isinstance(stack[-1], CNodeStringValue)):
            return False # shift
        if (3 <= len(stack)
            and isinstance(stack[-3], CNodeObjectList)
            and isinstance(stack[-2], CNodeComma)
            and isinstance(stack[-1], CNodeStringValue)):
            return False # shift
        if (3 <= len(stack)
            and isinstance(stack[-3], CNodeArrayList)
            and isinstance(stack[-2], CNodeComma)):
            # reduce
            stack[-3:] = [CNodeArrayList(*stack[-3:])] # type: ignore
            return True
        if (3 <= len(stack)
            and isinstance(stack[-3], CNodeStringValue)
            and isinstance(stack[-2], CNodeColon)):
            # reduce
            stack[-3:] = [CNodeNameValue(*stack[-3:])] # type: ignore
            return True
        raise ParseXception(stack[-1].start(), "Stray value (missing comma?)")
    if isinstance(stack[-1], CNodeArrayList):
        return False # shift
    if isinstance(stack[-1], CNodeNameValue):
        if 2 <= len(stack) and isinstance(stack[-2], CNodeLeftCurly):
            # reduce
            stack[-1:] = [CNodeObjectListStart(stack[-1])]
            return True
        if (3 <= len(stack)
            and isinstance(stack[-3], CNodeObjectList)
            and isinstance(stack[-2], CNodeComma)):
            # reduce
            stack[-3:] = [CNodeObjectList(*stack[-3:])] # type: ignore
            return True
        raise ParseXception(stack[-1].start(),
                            "Stray name:value (missing comma?)")
    if isinstance(stack[-1], CNodeObjectList):
        return False # shift

    raise ParseXception(stack[-1].start(),
                        f"Unexpected node: {type(stack[-1]).__name__}")


class CST:
    """CST: A Concrete Syntax Tree

    Attributes:
      - root: CNodeValue, the root node of the CST

    Methods:
      - tographviz(): Get a Graphviz representation of the tree.
    """
    root: CNodeValue

    def __init__(self, root: CNodeValue):
        """CST(root)

        Args:
          - root: CNodeValue, the root node of the CST
        """
        self.root = root

    def tographviz(self) -> str:
        """tographviz(): Get a Graphviz representation of the tree.

        Return: str, a Graphviz representation of the tree
        """
        return "digraph G {\n" + self.root.tographviz() + "}\n"


def parse(tokens: Iterable[Token]) -> CST:
    """parse(tokens): Parse a list of tokens into a CST.

    Args:
      - tokens: iterable of Token, the token list

    tokens will be exhausted at the start of this function.

    Return: CST, the concrete syntax tree

    Raise: ParseXception, in case of parsing issues
    """
    toshift = list(tokens)
    stack: list[CNode] = list()

    stack.append(shift(toshift))
    while toshift:
        if not reduce(stack):
            stack.append(shift(toshift))

    reduce(stack)
    while 1 < len(stack):
        if not reduce(stack):
            raise ParseXception(stack[-1].end(), "No more tokens to shift")

    if not isinstance(stack[0], CNodeValue):
        raise ParseXception(stack[0].start(), "Not a JSON value")

    return CST(stack[0])


if __name__ == "__main__":
    import sys
    try:
        from .lexer import JSONCString, lex, LexCeption
    except ImportError:
        if not TYPE_CHECKING:
            from lexer import JSONCString, lex, LexCeption
    if len(sys.argv) == 1 or {"-h", "-help", "--help"} & set(sys.argv):
        print(f"Usage: {sys.argv[0]} <JSONC file>")
        exit(0)

    with open(sys.argv[1]) as f:
        origin = JSONCString(f.read(), sys.argv[1])
    try:
        tokenlist = lex(origin)
        cst = parse(tokenlist.nocomments())
        print(cst.tographviz(), end='')
    except LexCeption as e:
        print(*e.args)
        exit(1)
    except ParseXception as e:
        print(*e.args)
        exit(1)
