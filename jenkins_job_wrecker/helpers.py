# encoding=utf8
import xml.etree.ElementTree as ET


def get_bool(txt):
    trues = ['true', 'True', 'Yes', 'yes', '1']
    return txt in trues


def gen_raw(xml, parent):
    raw = {}
    raw['xml'] = ET.tostring(xml)
    parent.append({'raw': raw})


class Mapper(object):
    def __init__(self, mapping):
        self._mapping = mapping

    def map_element(self, jjb_element, jjw_parent):
        element_mapping = self._mapping.get(jjb_element.tag)
        if element_mapping is None:
            return False

        if jjb_element.text is not None:
            jjw_parent[element_mapping[0]] = self._convert(jjb_element.text, element_mapping[1])
        return True

    def _convert(self, value, type_):
        if type_ == int:
            return int(value)
        elif type_ == str:
            return value
        elif type_ == bool:
            return get_bool(value)
        else:
            raise ValueError('Unsupported type: {}'.format(type_))


def replace_tab(s, tab_stop=4):
    result = str()
    pos = 0
    for c in s:
        if c == '\t':
            aligned = ((pos + tab_stop - 1) // tab_stop) * tab_stop
            if pos % tab_stop != 0:
                num_spaces = aligned - pos
            else:
                num_spaces = tab_stop
            co = ' ' * num_spaces
            pos += num_spaces
        else:
            co = c
            pos += 1
        result = result + co
    return result
