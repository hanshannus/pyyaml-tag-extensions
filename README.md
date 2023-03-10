# Yaml Tag Extensions (yamx)

- extend PyYaml's `SafeLoader` class with customized tags
- define decorators 

## Tags

Tags in Yaml files are indicated by a heading `!`. The following tags enable specialized handling of the subsequent node(s).

### !init

Initialize a python class or call a function from a python module without arguments or keywords.

```yaml
class: !init:package.Class
# import package.Class
# package.Class()
```

Initialize a python class or call a function from a python module with arguments.

```yaml
class: !init:package.Class
  - arg1
  - arg2
# import package.Class
# package.Class(arg1, arg2)
```

Initialize a python class or call a function from a python module with keywords.

```yaml
class: !init:package.Class
  kwarg1: value1
  kwarg2: value2
# import package.Class
# package.Class(kwarg1=value1, kwarg2=value2)
```

```yaml
class: !init:package.Class
  - arg
  - kwarg: value
# import package.Class
# package.Class(arg, kwarg=value)
```

### !import

A python module or class can be imported without initializing with this tag.

```yaml
class: !import:package.Class
```

### !from

Assuming that the file `file.yml` exists, and it contains the following:

```yaml
value: my_file.txt
```

The value `value` can be extracted with the `!from` tag and inserted into another (parent) YAML file.

```yaml
key: !from:/path/to/file.yml/value 
# key: my_file.txt
```

The file is detected automatically if a filename with suffix '.ylm' or '.yaml' exits, so the following is equivalent.

```yaml
key: !from:/path/to/file/value 
# key: my_file.txt
```

and if the file is the same directory

```yaml
key: !from:file/value 
# key: my_file.txt
```

it is also possible to import whole files

```yaml
key: !from:file
# key: 
#   value: my_file.txt
```

### Nested Tags

Nested tags are supported

```yaml
class: !init:package.Class
  - !from:file/value 
# import package.Class
# package.Class("my_file.txt")
```
