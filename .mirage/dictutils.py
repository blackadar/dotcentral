import collections
import pickle
from typing import Union


def set_dict_at(d: dict, label: str, val):
    """ Sets a nested dict value using dot label.

    Traverses a nested dict to set a value.
    If a level does not exist it will be created.
    :param d: Nested dict to update
    :param label: Dot String label
    :param val: Value to place
    :return: None
    """
    levels = label.split('.')
    if len(levels) == 1:
        d[levels[0]] = val
        return
    else:
        cur = d
        for level in levels[:-1]:
            cur = cur.setdefault(level, {})
        cur[levels[-1]] = val


def get_dict_at(d: dict, label: str):
    """ Gets value from a nested dict using dot label.

    Traverses a nested dict to get a value.
    :param d: Nested dict to traverse
    :param label: Dot String label
    :return: None
    """
    levels = label.split('.')
    if len(levels) == 1:
        return d[levels[0]]
    else:
        cur = d
        for level in levels[:-1]:
            cur = cur[level]
        return cur[levels[-1]]


def is_in_dict(d: dict, label: str):
    """ Tests if a label is present and has value in a dict using dot label.

    :param d: Nested dict to traverse
    :param label: Dot String label
    :return: True/False is in dict
    """
    try:
        val = get_dict_at(d, label)
        if val is None or val == '':
            return False
    except KeyError:
        return False

    return True


def update_nested_dict(original: dict, update: Union[dict, collections.abc.Mapping]):
    """ Updates a nested dictionary using another (sparse) nested dictionary.

    Imitates dict.update(), adding value if it doesn't exist or just modifying it.
    :param original: Dictionary to update
    :param update: Updates for Dictionary, as a Dictionary (can be sparse)
    :return: Updated Dictionary
    """
    # Iterate over each current-level item
    for k, v in update.items():
        # If the value is a Mapping, it's a next level which should be handled recursively
        if isinstance(v, collections.abc.Mapping):
            original[k] = update_nested_dict(original.get(k, {}), v)
        # Otherwise, it's the end of a recursive tree
        else:
            original[k] = v
    return original


def flatten(d, parent_key='', sep='.'):
    """
    Nested dict to flattened key dict.
    https://stackoverflow.com/questions/6027558/flatten-nested-dictionaries-compressing-keys
    :param d: dict to flatten
    :param parent_key: higher-level key not in dict
    :param sep: delimiter for nested keys
    :return: dict flattened dict
    """
    items = []
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, collections.MutableMapping):
            items.extend(flatten(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def to_file(data: dict, path: str):
    """ Writes a dict to a file using pickle.

    This function wraps pickle so that functionality can be replaced with an alternative easily.
    :param data: Python Dict
    :param path: Path to write the file
    :return: None
    """
    pickle.dump(data, open(path, "wb"))


def from_file(path: str):
    """ Reads a dict from a file using pickle.

    This function wraps pickle so that functionality can be replaced with an alternative easily.
    :param path: Path to read file from
    :return: Python Dict
    """
    return pickle.load(open(path, "rb"))
