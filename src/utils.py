def format_var_to_pythonic_type(_type:str, value):
  """
  Format a variable based on its type.

  Args:
      _type (str): Data type of the variable.
      value (any): Value to format.

  Returns:
      any: Formatted value.
  """
  if _type.lower() == "boolean" or _type.lower() == "bool":
      if isinstance(value, int):
          return bool(value)
      if isinstance(value, str):
          return value.lower() == "true"
  if _type.lower() == "integer" or _type.lower() == "int":
      if isinstance(value, str):
          return int(value)
  if _type.lower() == "text":
      if isinstance(value, str):
          if value.startswith("'") and value.endswith("'"):
              return format_var_to_pythonic_type(_type, value[1:-1])
          else:
              return value
  return value