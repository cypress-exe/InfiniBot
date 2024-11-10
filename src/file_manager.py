import os
import json

import logging

class JSONFile:
  def __init__(self, name):
    self.name = name
    self.file_name = f"{name}.json"
    self.path = f"./generated/configure/{self.file_name}"

  def ensure_existence(self):
    if not os.path.exists(self.path):
      logging.info(f"Creating {self.path}.")
      with open(self.path, "w") as file:
        file.write("{}")

    else:
      # Ensure file is not malformed
      try:
        with open(self.path, "r") as file:
          json.loads(file.read())
      except json.JSONDecodeError:
        logging.error(f"{self.path} is malformed. Deleting file.")
        os.remove(self.path)
        self.ensure_existence()

  def _get_data(self):
    self.ensure_existence()

    with open(self.path, "r") as file:
      return json.loads(file.read())
    
  def _set_data(self, data):
    self.ensure_existence()

    with open(self.path, "w") as file:
      file.write(json.dumps(data, indent=2))

  def __contains__(self, key):
    data = self._get_data()
    return key in data

  def __getitem__(self, key):
    data = self._get_data()

    if key not in self:
        raise KeyError(f"{key} does not exist in {self.file_name}.")

    return data[key]

  def __setitem__(self, key, value):
    data = self._get_data()

    if key not in self:
        raise KeyError(f"{key} does not exist in {self.file_name}. Use add_variable() method instead.")

    data[key] = value
    self._set_data(data)

  def __delitem__(self, key):
    data = self._get_data()

    if key not in self:
        raise KeyError(f"{key} does not exist in {self.file_name}.")
    
    del data[key]
    self._set_data(data)

  def __iter__(self):
    data = self._get_data()
    return iter(data)
  
  def __str__(self):
    data = self._get_data()
    return str(data)
  
  def __len__(self):
    data = self._get_data()
    return len(data)
  
  def __dict__(self):
    data = self._get_data()
    return data

  def add_variable(self, key, value):
    data = self._get_data()

    if key in self:
        raise KeyError(f"{key} already exists in {self.file_name}. Use __setitem__() instead. Implementation: JSONFile[key] = value")

    data[key] = value
    self._set_data(data)

  def delete_file(self):
    """Deletes the actual JSON file. Use with caution."""
    os.remove(self.path)
    logging.warning(f"Deleted {self.path}")