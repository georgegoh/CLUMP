#!/usr/bin/env python
# $Id: metadata.py 3517 2010-02-12 09:19:08Z kunalc $
#
# Copyright 2009 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

from xml.dom.minidom import *
from path import path
from kusu.util.errors import InvalidMetaXMLError, InvalidPathError, UnknownSettingNameError


META_XML_ROOT = '/opt/kusu/etc/'

class Metadata:
    def __init__(self, files=[]):
        if not files:
            files = path(META_XML_ROOT).files('*.meta.xml')

        self.files = files
        self.metadata = self._get_metadata()


    def _get_single_node_by_tag_name(self, parent_element, child_tag):
        curr_nodes = parent_element.getElementsByTagName(child_tag)
        if len(curr_nodes) != 1:
            file_path = parent_element.ownerDocument.documentURI
            raise InvalidMetaXMLError, "Missing a required tag: '%s' in file '%s'" % (child_tag, file_path)
        return curr_nodes[0]


    def _get_element_text_content(self, element):
        text = ''
        for sub_node in element.childNodes:
            if sub_node.nodeType == Node.TEXT_NODE:
                text += sub_node.data
        return text


    def _get_metadata(self):
        metadata = {}

        for file in self.files:
            try:
                file_path = path(file)
                file_path.size
            except:
                raise InvalidPathError, "File '%s' could not be read" % file_path

            doc = xml.dom.minidom.parse(file_path)
            doc.documentURI = str(file_path)
            for node in doc.getElementsByTagName('setting'):
                kname_node = self._get_single_node_by_tag_name(node, 'kname')
                kname = self._get_element_text_content(kname_node)

                name_node = self._get_single_node_by_tag_name(node, 'name')
                name = self._get_element_text_content(name_node)

                desc_node = self._get_single_node_by_tag_name(node, 'description')
                description = self._get_element_text_content(desc_node)

                allowed = ('', None)
                allowed_node = self._get_single_node_by_tag_name(node, 'allowed_values')
                allowed_type = allowed_node.getAttribute('type')
                allowed_data = None

                if allowed_type == 'list':
                    lst = []
                    for val_node in allowed_node.getElementsByTagName('value'):
                        val_desc = val_node.getAttribute('desc')
                        val_text = self._get_element_text_content(val_node)

                        lst.append((val_desc, val_text))
                    allowed_data = lst

                elif allowed_type == 'regex' or type == 'explanation':
                    allowed_data = self._get_element_text_content(allowed_node)

                allowed = (allowed_type, allowed_data)

                metadata[name] = {'kname': kname, 'desc': description, 'allows': allowed}
        self.metadata = metadata
        return self.metadata


    def displayMetadata(self, name=''):
        metadata = self.metadata
        if name:
            try:
                metadata = {name: self.metadata[name]}
            except KeyError:
                raise UnknownSettingNameError, "Setting '%s' was not recognized from the metadata" % name

        for item in metadata:
            print 'setting: ' + item
            print '\tdescription: %s' % self.metadata[item]['desc']

            allowed = self.metadata[item]['allows']
            allowed_type = allowed[0]
            if allowed_type == 'regex':
                print '\tallowed if values match %s: %s' % allowed

            elif allowed_type == 'explanation':
                print '\tallowed values %s: %s' % allowed

            elif allowed_type == 'list':
                print '\tallowed values list:'
                lst = allowed[1]
                for val in lst:
                    print '\t\t%s: %s' % val
            print


    def displayMetaNames(self):
        for name in self.metadata:
            print name

