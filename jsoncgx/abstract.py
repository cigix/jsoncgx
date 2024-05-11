#!/usr/bin/env python3

"""abstract.py: The JSON AST.

Functions:
  - abstract(cst): Turn a CST into an AST.

Classes:
  - ANodeValue and subclasses: Nodes in the AST
  - AST: An Abstract Syntax Tree
"""

from typing import TYPE_CHECKING, Any, Optional, cast

try:
    from .lexer import (Token, TokenLeftSquare, TokenRightSquare,
                        TokenLeftCurly, TokenRightCurly, TokenColon, TokenComma)
    from .parser import (CNodeLeftSquare, CNodeRightSquare, CNodeLeftCurly,
                         CNodeRightCurly, CNodeColon, CNodeComma, CNodeValue,
                         CNodeNumberValue, CNodeStringValue, CNodeBoolValue,
                         CNodeNullValue, CNodeArrayList, CNodeArrayListStart,
                         CNodeArray, CNodeNameValue, CNodeObjectList,
                         CNodeObjectListStart, CNodeObject, CST)
except ImportError:
    if not TYPE_CHECKING:
        from lexer import (Token, TokenLeftSquare, TokenRightSquare,
                           TokenLeftCurly, TokenRightCurly, TokenColon,
                           TokenComma)
        from parser import (CNodeLeftSquare, CNodeRightSquare, CNodeLeftCurly,
                            CNodeRightCurly, CNodeColon, CNodeComma, CNodeValue,
                            CNodeNumberValue, CNodeStringValue, CNodeBoolValue,
                            CNodeNullValue, CNodeArrayList, CNodeArrayListStart,
                            CNodeArray, CNodeNameValue, CNodeObjectList,
                            CNodeObjectListStart, CNodeObject, CST)

class ANodeValue:
    """ANodeValue: A node in the AST.

    Methods:
      - tographviz(): Get a Graphviz representation of the subtree.
    """
    def tographviz(_) -> str:
        """tographviz(): Get a Graphviz representation of the subtree.

        Return: str, a Graphviz representation of the subtree
        """
        raise NotImplementedError()


class ANodeLeaf(ANodeValue):
    """ANodeLeaf: A leaf node in the AST

    Attributes:
      - token: Token, the token associated to this leaf node value.

    Methods:
      - str(ANodeLeaf): alias for str(token)

      - value(): Get the value of this node.
    """
    token: Token

    def __init__(self, token: Token):
        """ANodeLeaf(token)

        Args:
          - token: Token, the token associated to this leaf node value.
        """
        self.token = token

    def __str__(self) -> str:
        return str(self.token)

    def value(_) -> Any:
        """value(): Get the value of this node."""
        raise NotImplementedError()


class ANodeNumber(ANodeLeaf):
    """ANodeNumber: An AST node for a JSON number.

    Methods:
      - float(ANodeNumber): Get the value.
      - int(ANodeNumber): Get the value.

      - value(): Get the value.
    """
    def __init__(self, nodenumber: CNodeNumberValue):
        """ANodeNumber(nodenumber)

        Args:
          - nodenumber: CNodeNumberValue, the concrete number node
        """
        super().__init__(nodenumber.number.start())

    def __float__(self) -> float:
        return float(str(self))

    def __int__(self) -> int:
        return int(str(self))

    def value(self) -> int | float:
        """value(): Get the value.

        Return: int or float, the value.
        """
        try:
            return int(self)
        except ValueError:
            return float(self)

    def tographviz(self) -> str:
        return f'  "{id(self)}" [label="{str(self)}" shape=box];\n'


class ANodeString(ANodeLeaf):
    """ANodeString: An AST node for a JSON string.

    Methods:
      - value(): alias for str(token)
    """
    def __init__(self, nodestring: CNodeStringValue):
        """ANodeString(nodestring)

        Args:
          - nodestring: CNodeStringValue, the concrete string node
        """
        super().__init__(nodestring.string.start())

    def value(self) -> str:
        return str(self)[1:-1]

    def tographviz(self) -> str:
        return f'  "{id(self)}" [label=<{str(self)}> shape=box];\n'


class ANodeBool(ANodeLeaf):
    """ANodeBool: An AST node for a JSON bool.

    Methods:
      - bool(ANodeBool): Get the boolean value for this node.

      - value(): alias for bool(ANodeBool)
    """
    def __init__(self, nodebool: CNodeBoolValue):
        """ANodeBool(nodebool)

        Args:
          - nodebool: CNodeBoolValue, the concrete bool node
        """
        super().__init__(nodebool.value.start())

    def __bool__(self) -> bool:
        return str(self) == "true"

    def value(self) -> bool:
        return bool(self)

    def tographviz(self) -> str:
        return f'  "{id(self)}" [label="{str(self)}" shape=box];\n'


class ANodeNull(ANodeLeaf):
    """ANodeNull: An AST node for a JSON null.

    Methods:
      - value(): None
    """
    def __init__(self, nodenull: CNodeNullValue):
        """ANodeNull(nodenull)

        Args:
          - nodenull: CNodeNullValue, the concrete null node
        """
        super().__init__(nodenull.value.start())

    def value(_) -> None:
        return None

    def tographviz(self) -> str:
        return f'  "{id(self)}" [label="{str(self)}" shape=box];\n'


class ANodeArray(ANodeValue):
    """ANodeArray: An AST node for a JSON array.

    Attributes:
      - leftbracket: TokenLeftSquare, the opening bracket token
      - values: list of ANodeValue, the list of values
      - commas: list of TokenComma, the list of comma tokens
      - rightbracket: TokenRightSquare, the closing bracket token

    Either both values and commas are empty, or len(values) == len(commas) + 1.
    """
    leftbracket: TokenLeftSquare
    values: list[ANodeValue]
    commas: list[TokenComma]
    rightbracket: TokenRightSquare

    def __init__(self, leftbracket: CNodeLeftSquare, values: list[ANodeValue],
                 commas: list[CNodeComma], rightbracket: CNodeRightSquare):
        """ANodeArray(leftbracket, values, commas, rightbracket)

        Args:
          - leftbracket: CNodeLeftSquare, the opening bracket concrete node
          - values: list of ANodeValue, the list of values
          - commas: list of CNodeComma, the list of comma concrete nodes
          - rightbracket: CNodeRightSquare, the closing bracket concrete node
        """
        self.leftbracket = cast(TokenLeftSquare, leftbracket.start())
        self.values = list(values)
        self.commas = list(cast(TokenComma, comma.start()) for comma in commas)
        self.rightbracket = cast(TokenRightSquare, rightbracket.end())

    def tographviz(self) -> str:
        graphviz = f'  "{id(self)}" [label=Array];\n'
        for value in self.values:
            graphviz += value.tographviz()
            graphviz += f'  "{id(self)}" -> "{id(value)}";\n'
        return graphviz


class ANodeObject(ANodeValue):
    """ANodeObject: An AST node for a JSON object.

    Attributes:
      - leftbracket: TokenLeftCurly, the opening bracket token
      - items: list of tuple (ANodeString, TokenColon, ANodeValue), the list of
        name:value pairs
      - commas: list of TokenComma, the list of comma tokens
      - rightbracket: TokenRightCurly, the closing bracket token

    Either both items and commas are empty, or len(items) == len(commas) + 1.
    """
    leftbracket: TokenLeftCurly
    items: list[tuple[ANodeString, TokenColon, ANodeValue]]
    commas: list[TokenComma]
    rightbracket: TokenRightCurly

    def __init__(self, leftbracket: CNodeLeftCurly,
                 items: list[tuple[ANodeString, CNodeColon, ANodeValue]],
                 commas: list[CNodeComma], rightbracket: CNodeRightCurly):
        """ANodeObject(leftbracket, items, commas, rightbracket)

        Args:
          - leftbracket: CNodeLeftCurly, the opening bracket concrete node
          - items: list of tuple (ANodeString, CNodeColon, ANodeValue), the list
            of name:value pairs
          - commas: list of CNodeComma, the list of comma concrete nodes
          - rightbracket: CNodeRightCurly, the closing bracket concrete node
        """
        self.leftbracket = cast(TokenLeftCurly, leftbracket.start())
        self.items = list()
        for item in items:
            colon = cast(TokenColon, item[1].start())
            self.items.append((item[0], colon, item[2]))
        self.commas = list(cast(TokenComma, comma.start()) for comma in commas)
        self.rightbracket = cast(TokenRightCurly, rightbracket.end())

    def tographviz(self) -> str:
        graphviz = f'  "{id(self)}" [label=Object];\n'
        for i, item in enumerate(self.items):
            identifier = str(id(self)) + f"({i})"
            graphviz += f'  "{identifier}" [label="" shape=point];\n'
            graphviz += f'  "{id(self)}" -> "{identifier}";\n'
            graphviz += item[0].tographviz()
            graphviz += f'  "{identifier}" -> "{id(item[0])}";\n'
            graphviz += item[2].tographviz()
            graphviz += f'  "{identifier}" -> "{id(item[2])}";\n'
        return graphviz


def abstractify(node: CNodeValue) -> ANodeValue:
    """abstractify(node): Make a concrete node abstract.

    Args:
      - node: CNodeValue

    Return: ANodeValue, the equivalent abstract subtree

    Raise: ValueError, if the node cannot be abstractified
    """
    if isinstance(node, CNodeNumberValue):
        return ANodeNumber(node)
    if isinstance(node, CNodeStringValue):
        return ANodeString(node)
    if isinstance(node, CNodeBoolValue):
        return ANodeBool(node)
    if isinstance(node, CNodeNullValue):
        return ANodeNull(node)

    if isinstance(node, CNodeArray):
        def flattenarr(node: CNodeArrayList | None
                       ) -> tuple[list[ANodeValue], list[CNodeComma]]:
            if node is None:
                return (list(), list())
            if isinstance(node, CNodeArrayListStart):
                return ([abstractify(node.value)], list())
            # CNodeArrayList
            values, commas = flattenarr(node.left)
            return (values + [abstractify(node.right)], commas + [node.comma])
        values, commas = flattenarr(node.values)
        return ANodeArray(node.leftbracket, values, commas, node.rightbracket)

    if isinstance(node, CNodeObject):
        def abstractnamevalue(node: CNodeNameValue
                              ) -> tuple[ANodeString, CNodeColon, ANodeValue]:
            aname = cast(ANodeString, abstractify(node.name))
            return (aname, node.colon, abstractify(node.value))
        def flattenobj(node: CNodeObjectList | None
                       ) -> tuple[list[tuple[ANodeString, CNodeColon,
                                             ANodeValue]], list[CNodeComma]]:
            if node is None:
                return (list(), list())
            if isinstance(node, CNodeObjectListStart):
                return ([abstractnamevalue(node.value)], list())
            # CNodeObjectList
            values, commas = flattenobj(node.left)
            return (values + [abstractnamevalue(node.right)],
                    commas + [node.comma])
        items, commas = flattenobj(node.items)
        return ANodeObject(node.leftbracket, items, commas, node.rightbracket)

    raise ValueError(f"Cannot abstractify value of type {type(node).__name__}")


class AST:
    """AST: An Abstract Syntax Tree

    Attributes:
      - root: ANodeValue, the root node of the AST

    Methods:
      - tographviz(): Get a Graphviz representation of the tree.
    """
    root: ANodeValue

    def __init__(self, root: ANodeValue):
        """AST(root)

        Args:
          - root: ANodeValue, the root node of the AST
        """
        self.root = root

    def tographviz(self) -> str:
        """tographviz(): Get a Graphviz representation of the tree.

        Return: str, a Graphviz representation of the tree
        """
        return "digraph G {\n" + self.root.tographviz() + "}\n"


def abstract(cst: CST) -> AST:
    """abstract(cst): Turn a CST into an AST.

    Args:
      - cst: CST

    Return: AST

    Raise: ValueError, if the CST is not suited for abstractification
    """
    return AST(abstractify(cst.root))


if __name__ == "__main__":
    import sys
    try:
        from .lexer import JSONCString, lex, LexCeption
        from .parser import parse, ParseXception
    except ImportError:
        if not TYPE_CHECKING:
            from lexer import JSONCString, lex, LexCeption
            from parser import parse, ParseXception
    if len(sys.argv) == 1 or {"-h", "-help", "--help"} & set(sys.argv):
        print(f"Usage: {sys.argv[0]} <JSONC file>")
        exit(0)

    with open(sys.argv[1]) as f:
        origin = JSONCString(f.read(), sys.argv[1])
    try:
        tokenlist = lex(origin)
        cst = parse(tokenlist.nocomments())
        ast = abstract(cst)
        print(ast.tographviz(), end='')
    except LexCeption as e:
        print(*e.args)
        exit(1)
    except ParseXception as e:
        print(*e.args)
        exit(1)
