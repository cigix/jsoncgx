# jsoncgx: An overpowered JSON-with-comments parser with inplace edition

## Cool, a JSONC parser for Python. How do I load my file into a `dict`?

I'll stop you right here. If you're only looking at simply deserialising JSONC
files, this library is not for you.

`jsoncgx` is developped with 3 intentions:
1. Supporting C-style `//` and C++-style `/**/` comments. This part is typical,
   there are lots of other libraries offering this functionality.
1. Offering more flexibility with the JSON syntax that your usual
   straight-to-Python-types parser. Namely, the JSON format allows to have
   multiple name:value pairs with the same name in the same object, but that is
   not supported by Python's `dict`s.
1. Inplace edition, that is, being able to replace a chunk of a given JSONC file
   without messing up its indentation or comments. Typically, libraries only
   offer indentation _imitation_, that is, deserialisation makes guesses about
   the indentation, and serialisation reproduces it.

## Installation

This library is [available on PyPI](https://pypi.org/project/jsoncgx/):

```
pip install --user jsoncgx
```

## Comparison / Quickstart / Demo

<table>
   <tr>
      <th></th>
      <th>Standard Python module</th>
<th>

`jsoncgx`

</th>
   </tr>
   <tr>
      <td>Loading JSON data</td>
<td>

```python
>>> import json
>>> data = json.loads('{ "answer": 42 }')
>>> data["answer"]
42
```

</td>
<td>

```python

>>> import jsoncgx
>>> editor = jsoncgx.loads('{ "answer": 42 }')
>>> editor.root["answer"][0]
42
```

</td>
   </tr>
   <tr>
      <td>Editing JSON data</td>
<td>

```python
>>> data["answer"] = "spam"
>>> json.dumps(data)
'{"answer": "spam"}'
```

</td>
<td>

```python
>>> editor.root.editreplacevalue(0, "spam")
>>> editor.dumps()
'{ "answer": "spam" }'
```

</td>
   </tr>
   <tr>
      <td>Working with JSON files</td>
<td>

```python
>>> with open("in.json") as f:
...   data = json.load(f)
...
>>> with open("out.json", "w") as f:
...   json.dump(data, f)
...
```

</td>
<td>

```python
>>> editor = json.loadf("in.json")
>>> editor.dumpf("out.json")
```
Or use `jsoncgx.load()` and `jsoncgx.JSONEditor.dump()` with a file handle, like the standard module.
</td>
   </tr>
   <tr>
      <td>Non unique name</td>
<td>

```python
>>> data = json.loads(
...     '{ "answer": 42, "answer": "spam" }')
>>> data["answer"]
'spam'
```

</td>
<td>

```python
>>> editor = jsoncgx.loads(
...     '{ "answer": 42, "answer": "spam" }')
>>> editor.root["answer"][0]
42
>>> editor.root["answer"][1]
'spam'
```

</td>
   </tr>
   <tr>
      <td>Comments</td>
<td>

```python
>>> data = json.loads(
...     '{ "answer": /* eggs and */ 42 }')
Traceback (most recent call last):
...
json.decoder.JSONDecodeError: ...
```

</td>
<td>

```python
>>> editor = jsoncgx.loads(
...     '{ "answer": /* eggs and */ 42 }')
>>> editor.root.editreplacevalue(0, "spam")
>>> editor.dumps()
'{ "answer": /* eggs and */ "spam" }'
```

</td>
   </tr>
</table>

## What syntax does this parse exactly?

[ECMA-404](https://ecma-international.org/wp-content/uploads/ECMA-404_2nd_edition_december_2017.pdf)
with the following additional lexical elements:
* regex `//[^\n]*\n`, that is, the Unicode scalar sequence:
  * U+002F,
  * U+002F,
  * any amount of any scalars except U+000A,
  * U+000A.
* lazy regex `/\*.*\*/`, that is, the Unicode scalar sequence:
  * U+002F,
  * U+002A,
  * any amount of any scalars except the sequence U+002A U+002F
  * U+002A,
  * U+002F.

Those elements are considered like whitespace.

## Architecture

![jsoncgx architecture](architecture.png)

## Changelog

### V1.1:

* `JSONNumber`, `JSONString`, `JSONBool`, and `JSONNull` have been replaced with
  `JSONBuiltin`, for easier integration.
* `edit*()` methods that accepted `JSONValue` now also accept `int`, `float`,
  `str`, `bool`, and `None`. They are automatically turned into `JSONBuiltin`.
