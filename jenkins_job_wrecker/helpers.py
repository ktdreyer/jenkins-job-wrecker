# encoding=utf8
import xml.etree.ElementTree as ET


def get_bool(txt):
    trues = ['true', 'True', 'Yes', 'yes', '1']
    return txt in trues


def gen_raw(xml, parent):
    raw = {}
    raw['xml'] = ET.tostring(xml)
    parent.append({'raw': raw})
