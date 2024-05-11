#!/usr/bin/env python3

"""rexel.py: The reverse JSONC lexer.

Functions:
  - editableify(anode, fragmentlist): Turn AST nodes into JSON values.
  - xel(jsonroot, fragmentlist): Reverse lex.

Classes:
  - Fragment and subclasses: Objects representing chunks of JSONC data
  - FragmentList: A list of Fragment
  - JSONEditor: Editable JSON data.
  - JSONValue and subclasses: Objects representing JSON values
"""

from __future__ import annotations

import random # for FragmentList.tohtml()
from os import PathLike
from typing import TYPE_CHECKING, Any, IO, Iterable, NamedTuple, TypeAlias, cast

try:
    from .lexer import JSONCString, Token
    from .abstract import (ANodeValue, ANodeNumber, ANodeString, ANodeBool,
                           ANodeNull, ANodeArray, ANodeObject, AST)
except ImportError:
    if not TYPE_CHECKING:
        from lexer import JSONCString, Token
        from abstract import (ANodeValue, ANodeNumber, ANodeString, ANodeBool,
                              ANodeNull, ANodeArray, ANodeObject, AST)

class Fragment:
    """Fragment: A chunk of JSONC data.

    Methods:
      - str(Fragment): the chunk of data
    """
    # Private attributes:
    #   - _content: str, the chunk of data
    _content: str

    def __init__(self, content: str):
        """Fragment(content)

        Args:
          - content: str, the chunk of data
        """
        self._content = content

    def __str__(self) -> str:
        return self._content


class FragmentOrigin(Fragment):
    """FragmentOrigin: A fragment that comes from a token in the original data.

    Methods:
      - origin(): Get the JSONCString the token comes from.
      - start(): Get the byte position of the start of the token in origin.
      - end(): Get the byte position directly after the token in origin.
    """
    # Private attributes:
    #   - _token: Token, the token this fragment comes from
    _token: Token

    def __init__(self, token: Token):
        """FragmentOrigin(token)

        Args:
          - token: Token, the token this fragment comes from
        """
        self._token = token
        super().__init__(str(token))

    def origin(self) -> JSONCString:
        """origin(): Get the JSONCString the token comes from.

        Return: JSONCString
        """
        return self._token.origin

    def start(self) -> int:
        """start(): Get the byte position of the start of the token in origin.

        Return: int
        """
        return self._token.start

    def end(self) -> int:
        """end(): Get the byte position directly after the token in origin.

        Return: int
        """
        return self._token.end


class FragmentFiller(Fragment):
    """FragmentFiller: A fragment of the original data that was not used in
    parsing.

    Class methods:
      - FragmentFiller.everythingbefore(other): Get all data before a token as
        filler.
      - FragmentFiller.between(before, after): Get all data between two tokens
        as filler.
      - FragmentFiller.everythingafter(other): Get all data after a token as
        filler.
    """
    def __init__(self, origin: JSONCString, start: int, end: int):
        """FragmentFiller(origin, start, end)

        Args:
          - origin: JSONCString, the original data
          - start: int, the byte position of the start of the filler
          - end: int, the byte position directly after the filler

        You should not call this constructor; you should rather use one of the
        class methods:
          - FragmentFiller.everythingbefore(other)
          - FragmentFiller.between(before, after)
          - FragmentFiller.everythingafter(other)
        """
        super().__init__(origin[start:end])

    @classmethod
    def everythingbefore(cls, other: FragmentOrigin) -> FragmentFiller:
        """FragmentFiller.everythingbefore(other): Get all data before a token
        as filler.

        Args:
          - other: FragmentOrigin, the token following the filler

        Return: FragmentFiller, the filler before the token
        """
        return cls(other.origin(), 0, other.start())

    @classmethod
    def between(cls, before: FragmentOrigin, after: FragmentOrigin
                ) -> FragmentFiller:
        """FragmentFiller.between(before, after): Get all data between two
        tokens as filler.

        Args:
          - before: FragmentOrigin, the token preceding the filler
          - after: FragmentOrigin, the token following the filler

        Return: FragmentFiller, the filler between the tokens.

        Raise: ValueError, if data cannot be got between tokens
        """
        origin = before.origin()
        if origin is not after.origin():
            raise ValueError("Tokens do not have the same origin")
        start = before.end()
        end = after.start()
        if end <= start:
            raise ValueError("No data between tokens")
        return cls(origin, start, end)

    @classmethod
    def everythingafter(cls, other: FragmentOrigin) -> FragmentFiller:
        """FragmentFiller.everythingafter(other): Get all data after a token as
        filler.

        Args:
          - other: FragmentOrigin, the token preceding the filler

        Return: FragmentFiller, the filler after the token
        """
        origin = other.origin()
        return cls(origin, other.end(), len(origin))


class FragmentEdit(Fragment):
    """FragmentEdit: A fragment that was created through edition."""
    pass


class FragmentEditFiller(FragmentEdit, FragmentFiller):
    """FragmentEditFiller: A filler fragment that was created through edition.

    Class methods:
      - FragmentEditFiller.copy(fillers): Copy fillers into new edit fillers.
    """
    def __init__(self, other: str):
        FragmentEdit.__init__(self, str(other))

    @classmethod
    def copy(cls, fillers: Iterable[FragmentFiller]
             ) -> list[FragmentEditFiller]:
        """FragmentEditFiller.copy(fillers): Copy fillers into new edit fillers.

        Args:
          - fillers: iterable of FragmentFiller, the fillers to copy

        Return: list of FragmentEditFiller, the new edit fillers.
        """
        return [cls(str(filler)) for filler in fillers]


class FragmentList:
    """FragmentList: A list of Fragment.

    The same fragment cannot be contained twice in the same FragmentList: you
    must use FragmentEdit to get copies.

    Methods:
      - len(FragmentList): Get the length of the list.
      - str(FragmentList): Concatenate all the fragments.
      - fragment in FragmentList: Is fragment in the list.
      - FragmentList & (list of Fragment): Is any of the fragments already in
        the list.

      - tohtml(): Get a HTML representation of the fragments.
      - append(fragment): Add a fragment to the end of the list.
      - insertat(index, fragment): Insert a fragment in the list.
      - getfillerbetween(startfragment, endfragment): Get the fillers between
        two fragments.
      - delete(startfragment, endfragment): Delete a part of the list.
      - insertbefore(fragment, toinsert): Insert fragments before one that is
        already in the list.
      - insertafter(fragment, toinsert): Insert fragments after one that is
        already in the list.
      - replace(startoldfragment, endoldfragment, newfragments): Replace a part
        of the list.
    """
    # Private attributes:
    #   - _fragments: list of Fragment, the fragment list
    _fragments: list[Fragment]

    def __init__(self) -> None:
        """FragmentList()"""
        self._fragments = list()

    def __len__(self) -> int:
        return len(self._fragments)

    def __str__(self) -> str:
        return ''.join(map(str, self._fragments))

    def __contains__(self, fragment: Fragment) -> bool:
        return fragment in self._fragments

    def __and__(self, fragments: Iterable[Fragment]) -> bool:
        return bool(set(self._fragments) & set(fragments))

    def tohtml(self) -> str:
        """tohtml(): Get a HTML representation of the fragments.

        Return: str, a HTML document representing the fragments.

        Each fragment is stylised with a random color, for better visualisation.
        """
        html = """<!DOCTYPE html>
<html>
  <head>
    <style>
code {
    white-space: pre;
    padding: 0 2px;
}
    </style>
  </head>
  <body>
    """
        for fragment in self._fragments:
            hue = random.randint(0, 359)
            style = f"background-color: hsl({hue} 100% 90%);"
            style += f"border: 1px solid hsl({hue} 100% 70%);"
            html += f'<code style="{style}">{fragment}</code>'
        html += """
  </body>
</html>
"""
        return html

    def append(self, fragment: Fragment) -> None:
        """append(fragment): Add a fragment to the end of the list.

        Args:
          - fragment: Fragment, the fragment to add.

        Raise: ValueError, if the fragment is already present in the list.
        """
        if fragment in self:
            raise ValueError("Fragment is already present in list")
        self._fragments.append(fragment)

    def insertat(self, index: int, fragment: Fragment) -> None:
        """insertat(index, fragment): Insert a fragment in the list.

        Args:
          - index: int, the position to insert at
          - fragment: Fragment, the fragment to insert

        Insertion is such that afterwards, fragment will be at position index in
        the list.

        If index is -1 or the length of the list, this is equivalent to
        append(fragment).

        Raise: ValueError, if index is not valid or fragment is already in the
        list.
        """
        if fragment in self:
            raise ValueError("Fragment is already present in list")
        if index == -1 or index == len(self._fragments):
            self._fragments.append(fragment)
        self._fragments.insert(index, fragment)

    def getfillerbetween(self, startfragment: Fragment, endfragment: Fragment
                         ) -> list[FragmentFiller]:
        """getfillerbetween(startfragment, endfragment): Get the fillers between
        two fragments.

        Args:
          - startfragment: Fragment, where to start
          - endfragment: Fragment, where to stop

        Return: list of FragmentFiller, may be empty, the fillers between
        startfragment and endfragment

        Even if startfragment or endfragment are FragmentFiller, they are not
        included in the result.

        Raise: ValueError, if startfragment or endfragment are not found in the
        list
        """
        start = self._fragments.index(startfragment)
        end = self._fragments.index(endfragment)
        return [fragment
                for fragment in self._fragments[start + 1:end]
                if isinstance(fragment, FragmentFiller)]

    def delete(self, startfragment: Fragment, endfragment: Fragment) -> None:
        """delete(startfragment, endfragment): Delete a part of the list.

        Args:
          - startfragment: Fragment, where to start
          - endfragment: Fragment, where to stop

        startfragment and endfragment are also deleted.

        Raise: ValueError, if startfragment or endfragment are not found in the
        list
        """
        start = self._fragments.index(startfragment)
        end = self._fragments.index(endfragment)
        del self._fragments[start:end + 1]

    def insertbefore(self, fragment: Fragment, toinsert: Iterable[Fragment]
                     ) -> None:
        """insertbefore(fragment, toinsert): Insert fragments before one that is
        already in the list.

        Args:
          - fragment: Fragment, the existing fragment
          - toinsert: list of Fragment, the fragments to insert

        Raise: ValueError, if fragment is not in the list or if any of toinsert
        is
        """
        if self & toinsert:
            raise ValueError("Fragment is already present in list")
        index = self._fragments.index(fragment)
        self._fragments[index:index] = toinsert

    def insertafter(self, fragment: Fragment, toinsert: Iterable[Fragment]
                    ) -> None:
        """insertafter(fragment, toinsert): Insert fragments after one that is
        already in the list.

        Args:
          - fragment: Fragment, the existing fragment
          - toinsert: list of Fragment, the fragments to insert

        Raise: ValueError, if fragment is not in the list or if any of the
        fragments to insert is
        """
        if self & toinsert:
            raise ValueError("Fragment is already present in list")
        index = self._fragments.index(fragment)
        self._fragments[index + 1:index + 1] = toinsert

    def replace(self, startoldfragment: Fragment, endoldfragment: Fragment,
                newfragments: Iterable[Fragment]) -> None:
        """replace(startoldfragment, endoldfragment, newfragments): Replace a
        part of the list.

        Args:
          - startoldfragment: Fragment, where to start
          - endoldfragment: Fragment, where to stop
          - newfragments: list of Fragment, the fragments to put in their place

        startfragment and endfragment are also replaced.

        Raise: ValueError, if startoldfragment or endoldfragment are not found
        in the list or if any of newfragments is
        """
        if self & newfragments:
            raise ValueError("Fragment is already present in list")
        start = self._fragments.index(startoldfragment)
        end = self._fragments.index(endoldfragment)
        self._fragments[start:end + 1] = newfragments


BuiltinType: TypeAlias = int | float | str | bool | None

class JSONValue:
    """JSONValue: A JSON value.

    This is an abstract type; see implementations:
      - JSONBuiltin
      - JSONArray
      - JSONObject

    Methods:
      - start(): Get the first fragment of the value.
      - end(): Get the last fragment of the value.
      - fragments(): Get the list of fragments of the value.
      - tographviz(): Get a Graphviz representation of the value.
    """
    def start(_) -> Fragment:
        """start(): Get the first fragment of the value.

        Return: Fragment, the first fragment of the value

        Note that this fragment may not be part of any FragmentList.
        """
        raise NotImplementedError()

    def end(_) -> Fragment:
        """end(): Get the last fragment of the value.

        Return: Fragment, the last fragment of the value

        Note that this fragment may not be part of any FragmentList.
        """
        raise NotImplementedError()

    def fragments(_) -> list[Fragment]:
        """fragments(): Get the list of fragments of the value.

        Return: list of Fragment, the fragments of the value

        Note that this list may not be part of any FragmentList, and does not
        include any FragmentFiller.
        """
        raise NotImplementedError()

    def tographviz(_) -> str:
        """tographviz(): Get a Graphviz representation of the subtree.

        Return: str, a Graphviz representation of the subtree
        """
        raise NotImplementedError()


class JSONBuiltin(JSONValue):
    """JSONBuiltin: A non-container JSON value.

    JSONBuiltin are a Python built-in type value, associated with a Fragment.
    They do not support edition; turn to a JSONContainer for that.

    Attributes:
      - value: int, float, str, bool, or None, the value
      - fragment: Fragment, the fragment

    Class methods:
      - create(value): Create a new JSONBuiltin.
    """
    value: BuiltinType
    fragment: Fragment

    def __init__(self, value: BuiltinType, fragment: Fragment):
        """JSONBuiltin(value, fragment)

        Args:
          - value: int, float, str, bool, or None, the value
          - fragment: Fragment, the fragment
        """
        self.value = value
        self.fragment = fragment

    @classmethod
    def create(cls, value: BuiltinType) -> JSONBuiltin:
        """JSONBuiltin.create(value): Create a new JSONBuiltin.

        Args:
          - value: int, float, str, bool, or None, the value

        Return: JSONBuiltin, the new JSONBuiltin

        Raise: ValueError, if value has an unsupported type.
        """
        match value:
            case int() | float():
                fragment = FragmentEdit(str(value))
            case str():
                fragment = FragmentEdit(f'"{value}"')
            case bool():
                fragment = FragmentEdit("true" if value else "false")
            case None:
                fragment = FragmentEdit("null")
            case _:
                raise ValueError("Cannot create JSONBuiltin from type "
                                 + type(value).__name__)
        return cls(value=value, fragment=fragment)

    def start(self) -> Fragment:
        return self.fragment

    def end(self) -> Fragment:
        return self.fragment

    def fragments(self) -> list[Fragment]:
        return [self.fragment]

    def tographviz(self) -> str:
        return f'  "{id(self)}" [label=<{self.fragment}> shape=box];\n'

    def __int__(self) -> int:
        return int(self.value) # type: ignore

    def __float__(self) -> float:
        return float(self.value) # type: ignore

    def __str__(self) -> str:
        return str(self.value)

    def __repr__(self) -> str:
        if isinstance(self.value, str):
            return repr(self.value)
        return str(self.fragment)


class JSONContainer:
    """JSONContainer: An editable JSON container.

    All JSONContainer are associated with a FragmentList with which they sync
    all insertions, deletions, and replacements within the container.
    """
    # Private attributes:
    #   - _fragmentlist: FragmentList, the list associated with the container
    _fragmentlist: FragmentList

    def __init__(self, fragmentlist: FragmentList):
        """JSONContainer(fragmentlist)

        Args:
          - fragmentlist: FragmentList, the list to associate with this
            container
        """
        self._fragmentlist = fragmentlist


class JSONArray(JSONValue, JSONContainer):
    """JSONArray: A JSON array.

    Methods:
      - len(JSONArray): Get the length of the array.
      - iter(JSONArray): Get an iterator over the values of the array.
      - JSONArray[index]: Get a value of the array.
      - JSONArray[slice]: Get a slice of values of the array.
      - JSONArray[index] = value: Alias for JSONArray.editreplace(index, value)
      - del JSONArray[index]: Alias for JSONArray.editdelete(index)

      - editdelete(index): Delete a value.
      - editinsert(index, value): Insert a value.
      - editinsertnewarray(index): Insert a new, empty array.
      - editinsertnewobject(index): Insert a new, empty object.
      - editreplace(index, newvalue): Replace a value.
      - editreplacenewarray(index): Replace a value with a new, empty array.
      - editreplacenewobject(index): Replace a value with a new, empty object.
    """
    # Private attributes:
    #   - _leftbracket: Fragment, the opening bracket fragment
    #   - _values: list of JSONValue, the list of values
    #   - _commas: list of Fragment, the list of commas
    #   - _rightbracket: Fragment, the closing bracket fragment
    # Either both _values and _commas are empty, or len(_values) == len(_commas)
    # + 1.
    _leftbracket: Fragment
    _values: list[JSONValue]
    _commas: list[Fragment]
    _rightbracket: Fragment

    def __init__(self, leftbracket: Fragment, values: list[JSONValue],
                 commas: list[Fragment], rightbracket: Fragment,
                 fragmentlist: FragmentList):
        """JSONArray(leftbracket, values, commas, rightbracket, fragmentlist)

        Args:
          - leftbracket: Fragment, the opening bracket fragment
          - values: list of JSONValue, the list of values
          - commas: list of Fragment, the list of commas
          - rightbracket: Fragment, the closing bracket fragment
          - fragmentlist: FragmentList, the fragment list associated with this
            container

        Raise: ValueError, if values and commas are neither both empty nor
        len(values) == len(commas) + 1.
        """
        if 0 < len(values) <= len(commas):
            raise ValueError("Too many commas")
        if len(commas) + 1 < len(values):
            raise ValueError("Not enough commas")
        self._leftbracket = leftbracket
        self._values = values
        self._commas = commas
        self._rightbracket = rightbracket
        JSONContainer.__init__(self, fragmentlist)

    def start(self) -> Fragment:
        return self._leftbracket

    def end(self) -> Fragment:
        return self._rightbracket

    def fragments(self) -> list[Fragment]:
        res = [self._leftbracket]
        for value, comma in zip(self._values, self._commas):
            res += value.fragments()
            res.append(comma)
        if self._values:
            res += self._values[-1].fragments()
        res.append(self._rightbracket)
        return res

    def tographviz(self) -> str:
        graphviz = f'  "{id(self)}" [label=Array];\n'
        for value in self._values:
            graphviz += value.tographviz()
            graphviz += f'  "{id(self)}" -> "{id(value)}";\n'
        return graphviz

    @classmethod
    def create(cls, fragmentlist: FragmentList) -> JSONArray:
        """create(fragmentlist): Create a new JSONArray.

        You probably don't want to use this method; see instead:
          - JSONArray.editinsertnewarray(index)
          - JSONArray.editreplacenewarray(index)
          - JSONObject.editinsertnewarray(index, name)
          - JSONObject.editreplacenewarray(index)
          - JSONEditor.newarray()
          - JSONEditor.editreplacewitharray()

        This method creates new FragmentEdit, but does not associate them with
        any FragmentList.

        Args:
          - fragmentlist: FragmentList, the fragment list to associate with the
            new container

        Return: JSONArray, the new JSON array
        """
        return cls(FragmentEdit("["), list(), list(), FragmentEdit("]"),
                   fragmentlist)

    def __len__(self) -> int:
        return len(self._values)

    def __iter__(self) -> Iterable[JSONValue]:
        return iter(self._values)

    def __getitem__(self, key: int | slice) -> JSONValue | list[JSONValue]:
        return self._values[key]

    def __setitem__(self, key: int, value: JSONValue | BuiltinType) -> None:
        self.editreplace(key, value)

    def __delitem__(self, key: int) -> None:
        self.editdelete(key)

    def editdelete(self, index: int) -> None:
        """editdelete(index): Delete a value.

        Args:
          - index: int, the position to delete

        If index is -1, this is equivalent to deleting the last element.

        Raise: IndexError, if index is not valid.

        Filler is reorganised around the deleted value:
        f is eventual filler, ^ is deleted fragments
        If array has 1 value:
             [ f1 value f2 ]
               ^^^^^^^^
          => [ f2 ]
        Else if deletion at the end:
             ... prev_value f1 , f2 value f3 ]
                               ^^^^^^^^^^
          => ... prev_value f1 f3 ]
        Else:
             ... prev_value f1 , f2 value f3 , f4 next_value ...
                                    ^^^^^^^^^^^^^
          => ... prev_value f1 , f2 next_value ...
        """
        if index == -1:
            index = len(self._values) - 1

        value = self._values[index]
        if len(self._values) == 1:
            #    [ f1 value f2 ]
            #      ^^^^^^^^
            # => [ f2 ]
            f1 = self._fragmentlist.getfillerbetween(self._leftbracket,
                                                     value.start())
            start = f1[0] if f1 else value.start()
            end = value.end()
            self._fragmentlist.delete(start, end)
            del self._values[0]
        elif index == len(self._values) - 1:
            #    ... prev_value f1 , f2 value f3 ]
            #                      ^^^^^^^^^^
            # => ... prev_value f1 f3 ]
            start = self._commas[-1]
            end = value.end()
            self._fragmentlist.delete(start, end)
            del self._values[-1]
            del self._commas[-1]
        else:
            #    ... prev_value f1 , f2 value f3 , f4 next_value ...
            #                           ^^^^^^^^^^^^^
            # => ... prev_value f1 , f2 next_value ...
            start = value.start()
            comma = self._commas[index]
            f4 = self._fragmentlist.getfillerbetween(
                    comma, self._values[index + 1].start())
            end = f4[-1] if f4 else comma
            self._fragmentlist.delete(start, end)
            del self._values[index]
            del self._commas[index]

    def editinsert(self, index: int, value: JSONValue | BuiltinType) -> None:
        """editinsert(index, value): Insert a value.

        Args:
          - index: int, the position to insert at
          - value: JSONValue, int, float, str, bool, or None, the value to
            insert

        Insertion is such that afterwards, value will be at position index in
        the array.

        If index is -1 or the length of the array, this is equivalent to
        inserting after the last element.

        All of the fragments of the value are registered with the FragmentList
        of the array. Notably, this will not include any filler they might have
        been associated with in another FragmentList.

        Raise:
          - IndexError, if index is not valid.
          - ValueError, if value has an unsupported type.

        Filler is reorganised around the inserted value:
        f is eventual filler, ^ is point of insertion, - is reused fragments
        If array is empty:
             [ f ]
               -^
          => [ f value f ]
        Else if insertion at the beginning:
             [ f start_value ...
               -^
          => [ f value , f start_value ...
        Else if insertion at the end and array has length 1:
             [ f1 end_value f2 ]
               --          ^
          => [ f1 end_value , f1 value f2 ]
        Else if insertion at the end:
             ... , f1 end_value f2 ]
                   --          ^
          => ... , f1 end_value , f1 value f2 ]
        Else:
             ... prev_value f1 , f2 next_value ...
                            --   --^
          => ... prev_value f1 , f2 value f1 , f2 next_value ...
        """
        assert -1 <= index <= len(self._values)
        if index == -1:
            index = len(self._values)

        if not isinstance(value, JSONValue):
            value = JSONBuiltin.create(value)

        if not self._values:
            #    [ f ]
            #      -^
            # => [ f value f ]
            f = self._fragmentlist.getfillerbetween(self._leftbracket,
                                                    self._rightbracket)
            toinsert = value.fragments()
            toinsert += FragmentEditFiller.copy(f)
            self._fragmentlist.insertbefore(self._rightbracket, toinsert)
            self._values.append(value)
        elif index == 0:
            #    [ f start_value ...
            #      -^
            # => [ f value , f start_value ...
            start_value = self._values[0]
            f = self._fragmentlist.getfillerbetween(self._leftbracket,
                                                    start_value.start())
            newcomma = FragmentEdit(",")
            toinsert = value.fragments()
            toinsert.append(newcomma)
            toinsert += FragmentEditFiller.copy(f)
            self._fragmentlist.insertbefore(start_value.start(), toinsert)
            self._values.insert(0, value)
            self._commas.insert(0, newcomma)
        elif len(self._values) == index:
            # If array has length 1:
            #    [ f0 end_value f2 ]
            #      --          ^
            # => [ f0 end_value , f1 value f2 ]
            # Else:
            #    ... , f0 end_value f2 ]
            #          --          ^
            # => ... , f0 end_value , f1 value f2 ]
            end_value = self._values[-1]
            if index == 1:
                f1 = self._fragmentlist.getfillerbetween(self._leftbracket,
                                                         end_value.start())
            else:
                f1 = self._fragmentlist.getfillerbetween(self._commas[-1],
                                                         end_value.start())
            newcomma = FragmentEdit(",")
            toinsert = [newcomma]
            toinsert += FragmentEditFiller.copy(f1)
            toinsert += value.fragments()
            self._fragmentlist.insertafter(end_value.end(), toinsert)
            self._values.append(value)
            self._commas.append(newcomma)
        else:
            #    ... prev_value f1 , f2 next_value ...
            #                   --   --^
            # => ... prev_value f1 , f2 value f1 , f2 next_value ...
            prev_value = self._values[index - 1]
            next_value = self._values[index]
            comma = self._commas[index - 1]
            f1 = self._fragmentlist.getfillerbetween(prev_value.end(), comma)
            f2 = self._fragmentlist.getfillerbetween(comma, next_value.start())
            comma = FragmentEdit(",")
            toinsert = value.fragments()
            toinsert += FragmentEditFiller.copy(f1)
            toinsert.append(comma)
            toinsert += FragmentEditFiller.copy(f2)
            self._fragmentlist.insertbefore(next_value.start(), toinsert)
            self._values.insert(index, value)
            self._commas.insert(index, comma)

    def editinsertnewarray(self, index: int) -> JSONArray:
        """editinsertnewarray(index): Insert a new, empty array.

        This is preferred to creating a new array, then inserting it.

        Args:
          - index: int, the position to insert at

        Return: JSONArray, the newly created array

        Raise: IndexError, if index is not valid.

        The new array has the same FragmentList as this container.
        """
        arr = JSONArray.create(self._fragmentlist)
        self.editinsert(index, arr)
        return arr

    def editinsertnewobject(self, index: int) -> JSONObject:
        """editinsertnewobject(index): Insert a new, empty object.

        This is preferred to creating a new object, then inserting it.

        Args:
          - index: int, the position to insert at

        Return: JSONObject, the newly created object

        Raise: IndexError, if index is not valid.

        The new object has the same FragmentList as this container.
        """
        obj = JSONObject.create(self._fragmentlist)
        self.editinsert(index, obj)
        return obj

    def editreplace(self, index: int, newvalue: JSONValue | BuiltinType
                    ) -> None:
        """editreplace(index, newvalue): Replace a value.

        Args:
          - index: int, the position to replace
          - newvalue: JSONValue, int, float, str, bool, or None, the new value

        Raise:
          - IndexError, if index is not valid.
          - ValueError, if value has an unsupported type.
        """
        if not isinstance(newvalue, JSONValue):
            newvalue = JSONBuiltin.create(newvalue)
        oldvalue = self._values[index]
        newfragments = newvalue.fragments()
        self._fragmentlist.replace(oldvalue.start(), oldvalue.end(),
                                   newfragments)
        self._values[index] = newvalue

    def editreplacenewarray(self, index: int) -> JSONArray:
        """editreplacenewarray(index): Replace a value with a new, empty array.

        This is preferred to creating a new array, then replacing a value with
        it.

        Args:
          - index: int, the position to replace

        Return: JSONArray, the newly created array

        Raise: IndexError, if index is not valid.

        The new array has the same FragmentList as this container.
        """
        arr = JSONArray.create(self._fragmentlist)
        self.editreplace(index, arr)
        return arr

    def editreplacenewobject(self, index: int) -> JSONObject:
        """editreplacenewobject(index): Replace a value with a new, empty
        object.

        This is preferred to creating a new object, then replacing a value with
        it.

        Args:
          - index: int, the position to replace

        Return: JSONObject, the newly created object

        Raise: IndexError, if index is not valid.

        The new object has the same FragmentList as this container.
        """
        obj = JSONObject.create(self._fragmentlist)
        self.editreplace(index, obj)
        return obj


class JSONObject(JSONValue, JSONContainer):
    """JSONObject: A JSON object.

    Methods:
      - len(JSONObject): Get the number of entries in the object.
      - iter(JSONObject): Alias for JSONObject.keys()
      - JSONObject[key]: Get the values of the object.
      - name in JSONObject: Is a name in the object.

      - keys(): Get the names of the object.
      - values(): Get the values of the object.
      - items(): Get the name:value entries of the object.
      - lookup(key): Get the indices of entries of the object.
      - editdelete(index): Delete an entry.
      - editinsert(index, name, value): Insert a new name:value entry.
      - editinsertnewarray(index, name): Insert an entry with a new, empty
        array.
      - editinsertnewobject(index, name): Insert an entry with a new, empty
        object.
      - editreplacename(index, newname): Replace the name of an entry.
      - editreplacevalue(index, newvalue): Replace the value of an entry.
      - editreplacenewarray(index): Replace the value of an entry with a new,
        empty array.
      - editreplacenewobject(index): Replace the value of an entry with a new,
        empty object.
    """
    # Private attributes:
    #   - _leftbracket: Fragment, the opening bracket fragment
    #   - _items: list of tuple (JSONBuiltin, Fragment, JSONValue), the (name,
    #     colon, value) entries
    #   - _commas: list of Fragment, the list of commas
    #   - _rightbracket: Fragment, the closing bracket fragment
    # Either both _items and _commas are empty, or len(_items) == len(_commas) +
    # 1.
    _leftbracket: Fragment
    _items: list[tuple[JSONBuiltin, Fragment, JSONValue]]
    _commas: list[Fragment]
    _rightbracket: Fragment

    def __init__(self, leftbracket: Fragment,
                 items: list[tuple[JSONBuiltin, Fragment, JSONValue]],
                 commas: list[Fragment], rightbracket: Fragment,
                 fragmentlist: FragmentList):
        """JSONObject(leftbracket, items, commas, rightbracket, fragmentlist)

        Args:
          - leftbracket: Fragment, the opening bracket fragment
          - items: list of tuple (JSONBuiltin, Fragment, JSONValue), the (name,
            colon, value) entries
          - commas: list of Fragment, the list of commas
          - rightbracket: Fragment, the closing bracket fragment
          - fragmentlist: FragmentList, the fragment list associated with this
            container

        Raise: ValueError, if items and commas are neither both empty nor
        len(items) == len(commas) + 1, or if the names are not all strings.
        """
        if 0 < len(items) <= len(commas):
            raise ValueError("Too many commas")
        if len(commas) + 1 < len(items):
            raise ValueError("Not enough commas")
        if not all(isinstance(name.value, str) for name, _, __ in items):
            raise ValueError("Names must be str")
        self._leftbracket = leftbracket
        self._items = items
        self._commas = commas
        self._rightbracket = rightbracket
        JSONContainer.__init__(self, fragmentlist)

    def start(self) -> Fragment:
        return self._leftbracket

    def end(self) -> Fragment:
        return self._rightbracket

    def fragments(self) -> list[Fragment]:
        res = [self._leftbracket]
        for item, comma in zip(self._items, self._commas):
            res += item[0].fragments()
            res.append(item[1])
            res += item[2].fragments()
            res.append(comma)
        if self._items:
            item = self._items[-1]
            res += item[0].fragments()
            res.append(item[1])
            res += item[2].fragments()
        res.append(self._rightbracket)
        return res

    def tographviz(self) -> str:
        graphviz = f'  "{id(self)}" [label=Object];\n'
        for i, item in enumerate(self._items):
            identifier = str(id(self)) + f"({i})"
            graphviz += f'  "{identifier}" [label="" shape=point];\n'
            graphviz += f'  "{id(self)}" -> "{identifier}";\n'
            graphviz += item[0].tographviz()
            graphviz += f'  "{identifier}" -> "{id(item[0])}";\n'
            graphviz += item[2].tographviz()
            graphviz += f'  "{identifier}" -> "{id(item[2])}";\n'
        return graphviz

    @classmethod
    def create(cls, fragmentlist: FragmentList) -> JSONObject:
        """create(fragmentlist): Create a new JSONObject.

        You probably don't want to use this method; see instead:
          - JSONArray.editinsertnewobject(index)
          - JSONArray.editreplacenewobject(index)
          - JSONObject.editinsertnewobject(index, name)
          - JSONObject.editreplacenewobject(index)
          - JSONEditor.newobject()
          - JSONEditor.editreplacewithobject()

        This method creates new FragmentEdit, but does not associate them with
        any FragmentList.

        Args:
          - fragmentlist: FragmentList, the fragment list to associate with the
            new container

        Return: JSONObject, the new JSON object
        """
        return cls(FragmentEdit("{"), list(), list(), FragmentEdit("}"),
                   fragmentlist)

    def __len__(self) -> int:
        return len(self._items)

    def __iter__(self) -> Iterable[str]:
        return self.keys()

    def __getitem__(self, key: str | JSONBuiltin) -> list[JSONValue]:
        return [value
                for name, _, value in self._items
                if str(name) == str(key)]

    def __contains__(self, key: str | JSONBuiltin) -> bool:
        key = str(key)
        return any(key == str(name) for name, _, __ in self._items)

    def keys(self) -> Iterable[str]:
        """keys(): Get the names of the object.

        Return: iterable of str, the names in the object

        Names can appear multiple times.
        """
        return (str(name) for name, _, __ in self._items)

    def values(self) -> Iterable[JSONValue]:
        """values(): Get the values of the object.

        Return: iterable of JSONValue, the values in the object
        """
        return (value for _, __, value in self._items)

    def items(self) -> Iterable[tuple[str, JSONValue]]:
        """items(): Get the name:value entries of the object.

        Return: iterable of tuple (str, JSONValue), the name:value entries of
        the array.
        """
        return ((str(name), value) for name, _, value in self._items)

    def lookup(self, key: str | JSONBuiltin) -> Iterable[int]:
        """lookup(key): Get the indices of entries of the object.

        Return: iterable of int, the indices of the entries that have this name
        """
        key = str(key)
        return (i
                for i, (name, _, __) in enumerate(self._items)
                if key == str(name))

    def editdelete(self, index: int) -> None:
        """editdelete(index): Delete an entry.

        Args:
          - index: int, the position to delete

        If index is -1, this is equivalent to deleting the last entry.

        Raise: IndexError, if index is not valid.

        Filler is reorganised around the deleted value, see
        JSONArray.editdelete().
        """
        if index == -1:
            index = len(self._items) - 1

        item = self._items[index]
        if len(self._items) == 1:
            f1 = self._fragmentlist.getfillerbetween(self._leftbracket,
                                                     item[0].start())
            start = f1[0] if f1 else item[0].start()
            end = item[2].end()
            self._fragmentlist.delete(start, end)
            del self._items[0]
        elif index == len(self._items) - 1:
            start = self._commas[-1]
            end = item[2].end()
            self._fragmentlist.delete(start, end)
            del self._items[-1]
            del self._commas[-1]
        else:
            start = item[0].start()
            comma = self._commas[index]
            f4 = self._fragmentlist.getfillerbetween(
                    comma, self._items[index + 1][0].start())
            end = f4[-1] if f4 else comma
            self._fragmentlist.delete(start, end)
            del self._items[index]
            del self._commas[index]

    def editinsert(self, index: int, name: str, value: JSONValue | BuiltinType
                   ) -> None:
        """editinsert(index, name, value): Insert a new name:value entry.

        Args:
          - index: int, the position to insert at
          - name: str, the name of the entry to insert
          - value: JSONValue, int, float, str, bool, or None, the value to
            insert

        Insertion is such that afterwards, the inserted entry will be at
        position index in the object.

        If index is -1 or the length of the object, this is equivalent to
        inserting after the last entry.

        All of the fragments of the value are registered with the FragmentList
        of the object. Notably, this will not include any filler they might have
        been associated with in another FragmentList.

        Raise:
          - IndexError, if index is not valid.
          - ValueError, if value has an unsupported type.

        Filler is reorganised around the inserted value:
        f is eventual filler, ^ is point of insertion, - is reused fragments
        If object is empty:
             [ f ]
               -^
          => [ f name : value f ]
        Else if insertion at the beginning:
             [ f1 start_name f2 : f3 start_value ...
               --^           --   --
          => [ f1 name f2 : f3 value , f1 start_name f2 : f3 start_value ...
        Else if insertion at the end and object has length 1:
             [ f1 end_name f2 : f3 end_value f4 ]
               --          --   --          ^
          => [ f1 end_name f2 : f3 end_value , f1 name f2 : f3 value f4 ]
        Else if insertion at the end:
             ... , f1 end_name f2 : f3 end_value f4 ]
                   --          --   --          ^
          => ... , f1 end_name f2 : f3 end_value , f1 name f2 : f3 value f4 ]
        Else:
             ... prev_name f1 : f2 prev_value f3 , f4 next_name ...
                           --   --            --   --^
          => ... prev_name f1 : f2 prev_value f3 , f4 name f1 : f2 value f3 , f4 next_name ...
        """
        assert -1 <= index <= len(self._items)
        if index == -1:
            index = len(self._items)

        jname = JSONBuiltin.create(name)
        if not isinstance(value, JSONValue):
            value = JSONBuiltin.create(value)
        colon = FragmentEdit(":")
        if not self._items:
            #    [ f ]
            #      -^
            # => [ f name : value f ]
            f = self._fragmentlist.getfillerbetween(self._leftbracket,
                                                    self._rightbracket)
            toinsert = jname.fragments()
            toinsert.append(colon)
            toinsert += value.fragments()
            toinsert += FragmentEditFiller.copy(f)
            self._fragmentlist.insertbefore(self._rightbracket, toinsert)
            self._items.append((jname, colon, value))
        elif index == 0:
            #    [ f1 start_name f2 : f3 start_value ...
            #      --^           --   --
            # => [ f1 name f2 : f3 value , f1 start_name f2 : f3 start_value ...
            start_item = self._items[0]
            f1 = self._fragmentlist.getfillerbetween(self._leftbracket,
                                                     start_item[0].start())
            f2 = self._fragmentlist.getfillerbetween(start_item[0].end(),
                                                     start_item[1])
            f3 = self._fragmentlist.getfillerbetween(start_item[1],
                                                     start_item[2].start())
            newcomma = FragmentEdit(",")
            toinsert = jname.fragments()
            toinsert += FragmentEditFiller.copy(f2)
            toinsert.append(colon)
            toinsert += FragmentEditFiller.copy(f3)
            toinsert += value.fragments()
            toinsert.append(newcomma)
            toinsert += FragmentEditFiller.copy(f1)
            self._fragmentlist.insertbefore(start_item[0].start(), toinsert)
            self._items.insert(0, (jname, colon, value))
            self._commas.insert(0, newcomma)
        elif len(self._items) == index:
            # If object has length 1:
            #    [ f1 end_name f2 : f3 end_value f4 ]
            #      --          --   --          ^
            # => [ f1 end_name f2 : f3 end_value , f1 name f2 : f3 value f4 ]
            # Else:
            #    ... , f1 end_name f2 : f3 end_value f4 ]
            #          --          --   --          ^
            # => ... , f1 end_name f2 : f3 end_value , f1 name f2 : f3 value f4 ]
            end_item = self._items[-1]
            if index == 1:
                f1 = self._fragmentlist.getfillerbetween(self._leftbracket,
                                                         end_item[0].start())
            else:
                f1 = self._fragmentlist.getfillerbetween(self._commas[-1],
                                                         end_item[0].start())
            f2 = self._fragmentlist.getfillerbetween(end_item[0].end(),
                                                     end_item[1])
            f3 = self._fragmentlist.getfillerbetween(end_item[1],
                                                     end_item[2].start())
            newcomma = FragmentEdit(",")
            toinsert = [newcomma]
            toinsert += FragmentEditFiller.copy(f1)
            toinsert += jname.fragments()
            toinsert += FragmentEditFiller.copy(f2)
            toinsert.append(colon)
            toinsert += FragmentEditFiller.copy(f3)
            toinsert += value.fragments()
            self._fragmentlist.insertafter(end_item[2].end(), toinsert)
            self._items.append((jname, colon, value))
            self._commas.append(newcomma)
        else:
            #    ... prev_name f1 : f2 prev_value f3 , f4 next_name ...
            #                  --   --            --   --^
            # => ... prev_name f1 : f2 prev_value f3 , f4 name f1 : f2 value f3 , f4 next_name ...
            prev_item = self._items[index - 1]
            next_item = self._items[index]
            comma = self._commas[index - 1]
            f1 = self._fragmentlist.getfillerbetween(prev_item[0].end(),
                                                     prev_item[1])
            f2 = self._fragmentlist.getfillerbetween(prev_item[1],
                                                     prev_item[2].start())
            f3 = self._fragmentlist.getfillerbetween(prev_item[2].end(), comma)
            f4 = self._fragmentlist.getfillerbetween(comma,
                                                     next_item[0].start())
            new_comma = FragmentEdit(",")
            toinsert = jname.fragments()
            toinsert += FragmentEditFiller.copy(f1)
            toinsert.append(colon)
            toinsert += FragmentEditFiller.copy(f2)
            toinsert += value.fragments()
            toinsert += FragmentEditFiller.copy(f3)
            toinsert.append(new_comma)
            toinsert += FragmentEditFiller.copy(f4)
            self._fragmentlist.insertbefore(next_item[0].start(), toinsert)
            self._items.insert(index, (jname, colon, value))
            self._commas.insert(index, new_comma)

    def editinsertnewarray(self, index: int, name: str) -> JSONArray:
        """editinsertnewarray(index, name): Insert an entry with a new, empty
        array.

        This is preferred to creating a new array, then inserting it.

        Args:
          - index: int, the position to insert at
          - name: str, the name of the entry to insert

        Return: JSONArray, the newly created array

        Raise: IndexError, if index is not valid.

        The new array has the same FragmentList as this container.
        """
        arr = JSONArray.create(self._fragmentlist)
        self.editinsert(index, name, arr)
        return arr

    def editinsertnewobject(self, index: int, name: str) -> JSONObject:
        """editinsertnewobject(index, name): Insert an entry with a new, empty
        object.

        This is preferred to creating a new object, then inserting it.

        Args:
          - index: int, the position to insert at
          - name: str, the name of the entry to insert

        Return: JSONObject, the newly created object

        Raise: IndexError, if index is not valid.

        The new object has the same FragmentList as this container.
        """
        obj = JSONObject.create(self._fragmentlist)
        self.editinsert(index, name, obj)
        return obj

    def editreplacename(self, index: int, newname: str) -> None:
        """editreplacename(index, newname): Replace the name of an entry.

        Args:
          - index: int, the position to replace
          - newname: str, the new name

        Raise: IndexError, if index is not valid.
        """
        oldname, colon, value = self._items[index]
        jnewname = JSONBuiltin.create(newname)
        newfragments = jnewname.fragments()
        self._fragmentlist.replace(oldname.start(), oldname.end(), newfragments)
        self._items[index] = (jnewname, colon, value)

    def editreplacevalue(self, index: int, newvalue: JSONValue | BuiltinType
                         ) -> None:
        """editreplacevalue(index, newvalue): Replace the value of an entry.

        Args:
          - index: int, the position to replace
          - newvalue: JSONValue, int, float, str, bool, or None, the new value

        Raise:
          - IndexError, if index is not valid.
          - ValueError, if value has an unsupported type.
        """
        if not isinstance(newvalue, JSONValue):
            newvalue = JSONBuiltin.create(newvalue)
        name, colon, oldvalue = self._items[index]
        newfragments = newvalue.fragments()
        self._fragmentlist.replace(oldvalue.start(), oldvalue.end(),
                                   newfragments)
        self._items[index] = (name, colon, newvalue)

    def editreplacenewarray(self, index: int) -> JSONArray:
        """editreplacenewarray(index): Replace the value of an entry with a new,
        empty array.

        This is preferred to creating a new array, then replacing a value with
        it.

        Args:
          - index: int, the position to replace

        Return: JSONArray, the newly created array

        Raise: IndexError, if index is not valid.

        The new array has the same FragmentList as this container.
        """
        arr = JSONArray.create(self._fragmentlist)
        self.editreplacevalue(index, arr)
        return arr

    def editreplacenewobject(self, index: int) -> JSONObject:
        """editreplacenewobject(index): Replace the value of an entry with a
        new, empty object.

        This is preferred to creating a new object, then replacing a value with
        it.

        Args:
          - index: int, the position to replace

        Return: JSONObject, the newly created object

        Raise: IndexError, if index is not valid.

        The new object has the same FragmentList as this container.
        """
        obj = JSONObject.create(self._fragmentlist)
        self.editreplacevalue(index, obj)
        return obj


def xel(jsonroot: JSONValue, fragmentlist: FragmentList) -> None:
    """xel(jsonroot, fragmentlist): Reverse lex.

    Build up a FragmentList from an original JSON AST, including the fillers.

    Args:
      - jsonroot: JSONValue, the AST root
      - fragmentlist: FragmentList, the empty fragment list to build up

    Raise: ValueError, if:
      - not all framgents in the AST are FragmentOrigin
      - not all fragments in the AST have the same origin
      - fragmentlist is not empty

    All the fragments of jsonroot will be registered to fragmentlist. If there
    are containers in the AST that are associated to a different FragmentList,
    edit operations on those containers will not update fragmentlist.
    """
    if len(fragmentlist) != 0:
        raise ValueError("fragmentlist should be empty")
    fragments = jsonroot.fragments()
    if not all(isinstance(fragment, FragmentOrigin) for fragment in fragments):
        raise ValueError("fragments should all be FragmentOrigin")
    ofragments = cast(list[FragmentOrigin], fragments)
    origins = {fragment.origin() for fragment in ofragments}
    if 1 < len(origins):
        raise ValueError("fragments shoul all have the same origin")
    origin = origins.pop()

    if 0 < ofragments[0].start():
        fragmentlist.append(FragmentFiller.everythingbefore(ofragments[0]))
    for i in range(len(ofragments) - 1):
        fragmentlist.append(ofragments[i])
        if ofragments[i].end() < ofragments[i + 1].start():
            fragmentlist.append(FragmentFiller.between(ofragments[i],
                                                       ofragments[i + 1]))
    fragmentlist.append(ofragments[-1])
    if ofragments[-1].end() < len(origin):
        fragmentlist.append(FragmentFiller.everythingafter(ofragments[-1]))


def editableify(anode: ANodeValue, fragmentlist: FragmentList) -> JSONValue:
    """editableify(anode, fragmentlist): Turn AST nodes into JSON values.

    Args:
      - anode: ANodeValue, the AST node to make editable
      - fragmentlist: FragmentList, the fragment list editable containers should
        be associated with

    Only FragmentOrigin will be produced. They will not be registered to
    fragmentlist, you should call xel() after this function.

    Return: JSONValue, the editable JSON value
    """
    match anode:
        case ANodeNumber() | ANodeString() | ANodeBool() | ANodeNull():
            return JSONBuiltin(value=anode.value(),
                               fragment=FragmentOrigin(anode.token))
        case ANodeArray():
            leftbracket = FragmentOrigin(anode.leftbracket)
            values = list(editableify(value, fragmentlist)
                          for value in anode.values)
            arrcommas: list[Fragment] = list(
                    FragmentOrigin(comma) for comma in anode.commas)
            rightbracket = FragmentOrigin(anode.rightbracket)
            return JSONArray(leftbracket, values, arrcommas, rightbracket,
                             fragmentlist)
        case ANodeObject():
            leftbracket = FragmentOrigin(anode.leftbracket)
            items = list()
            for item in anode.items:
                name = cast(JSONBuiltin, editableify(item[0], fragmentlist))
                colon: Fragment = FragmentOrigin(item[1])
                value = editableify(item[2], fragmentlist)
                items.append((name, colon, value))
            objcommas: list[Fragment] = list(
                    FragmentOrigin(comma) for comma in anode.commas)
            rightbracket = FragmentOrigin(anode.rightbracket)
            return JSONObject(leftbracket, items, objcommas, rightbracket,
                              fragmentlist)

    raise ValueError(f"Unrecognised AST node type: {type(anode).__name__}")


class JSONEditor(JSONContainer):
    """JSONEditor: Editable JSON data.

    Attributes:
      - root: JSONValue, the root of the editable AST

    Class methods:
      - JSONEditor.fromAST(ast): Make an AST editable.
      - JSONEditor.newarray(): Make a new editor.
      - JSONEditor.newobject(): Make a new editor.

    Methods:
      - tographviz(): Get a Graphviz representation of the tree.
      - editreplacewitharray(): Replace the root with an array.
      - editreplacewithobject(): Replace the root with an object.
      - dumps(): Compile a JSONC string.
      - dump(fp): Compile a JSONC file.
      - dumpf(path): Compile a JSONC file.
    """
    root: JSONValue

    def __init__(self, root: JSONValue, fragmentlist: FragmentList):
        """JSONEditor(root, fragmentlist)

        You probably don't want to use this method; see instead:
          - JSONEditor.fromAST(ast)
          - JSONEditor.newarray()
          - JSONEditor.newobject():

        Args:
          - root: JSONValue, the root of the editable AST
          - fragmentlist: FragmentList, the fragment list for this container
        """
        self.root = root
        super().__init__(fragmentlist)

    @classmethod
    def fromAST(cls, ast: AST) -> JSONEditor:
        """JSONEditor.fromAST(ast): Make an AST editable.

        Args:
          - ast: AST, an AST

        Return: JSONEditor, an editable AST.

        Raise: ValueError, if the AST does not come from regular lexing,
        parsing, and abstracting (see editableify() and xel()).

        This editor will retain all the whitespace and comments of the origin
        JSONCString, even through edition.
        """
        fragmentlist = FragmentList()
        root = editableify(ast.root, fragmentlist)
        xel(root, fragmentlist)
        return cls(root, fragmentlist)

    @classmethod
    def newarray(cls) -> JSONEditor:
        """JSONEditor.newarray(): Make a new editor.

        Return: JSONEditor, a new editable AST with an empty array at its root
        """
        fragmentlist = FragmentList()
        root = JSONArray.create(fragmentlist)
        for fragment in root.fragments():
            fragmentlist.append(fragment)
        return cls(root, fragmentlist)

    @classmethod
    def newobject(cls) -> JSONEditor:
        """JSONEditor.newobject(): Make a new editor.

        Return: JSONEditor, a new editable AST with an empty object at its root
        """
        fragmentlist = FragmentList()
        root = JSONObject.create(fragmentlist)
        for fragment in root.fragments():
            fragmentlist.append(fragment)
        return cls(root, fragmentlist)

    def tographviz(self) -> str:
        """tographviz(): Get a Graphviz representation of the tree.

        Return: str, a Graphviz representation of the tree
        """
        return "digraph G {\n" + self.root.tographviz() + "}\n"

    def editreplacewitharray(self) -> None:
        """editreplacewitharray(): Replace the root with an array."""
        oldroot = self.root
        newroot = JSONArray.create(self._fragmentlist)
        newfragments = newroot.fragments()
        self._fragmentlist.insertafter(oldroot.end(), newfragments)
        self._fragmentlist.delete(oldroot.start(), oldroot.end())
        self.root = newroot

    def editreplacewithobject(self) -> None:
        """editreplacewithobject(): Replace the root with an object."""
        oldroot = self.root
        newroot = JSONObject.create(self._fragmentlist)
        newfragments = newroot.fragments()
        self._fragmentlist.insertafter(oldroot.end(), newfragments)
        self._fragmentlist.delete(oldroot.start(), oldroot.end())
        self.root = newroot

    def dumps(self) -> str:
        """dumps(): Compile a JSONC string.

        Return: str, the JSONC data
        """
        return str(self._fragmentlist)

    def dump(self, fp: IO[str]) -> None:
        """dump(fp): Compile a JSONC file.

        Args:
          - fp: a .write() supporting object, the JSONC destination

        Alias for:
          fp.write(JSONEditor.dumps())
        """
        fp.write(self.dumps())

    def dumpf(self, path: PathLike) -> None:
        """dumpf(path): Compile a JSONC file.

        Args:
          - path: path-like object, the file to write

        Alias for:
          with open(path, "w") as f:
              f.write(JSONEditor.dumps())
        """
        with open(path, "w") as f:
            f.write(self.dumps())


if __name__ == "__main__":
    import sys
    try:
        from .lexer import JSONCString, lex, LexCeption
        from .parser import parse, ParseXception
        from .abstract import abstract
    except ImportError:
        if not TYPE_CHECKING:
            from lexer import JSONCString, lex, LexCeption
            from parser import parse, ParseXception
            from abstract import abstract
    if len(sys.argv) == 1 or {"-h", "-help", "--help"} & set(sys.argv):
        print(f"Usage: {sys.argv[0]} <JSONC file>")
        exit(0)

    with open(sys.argv[1]) as f:
        origin = JSONCString(f.read(), sys.argv[1])
    try:
        tokenlist = lex(origin)
        cst = parse(tokenlist.nocomments())
        ast = abstract(cst)
        editable = JSONEditor.fromAST(ast)
        print(editable.tographviz(), end='')
    except LexCeption as e:
        print(*e.args)
        exit(1)
    except ParseXception as e:
        print(*e.args)
        exit(1)
