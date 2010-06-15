#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2010 Platform Computing Inc.
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of version 2 of the GNU General Public License as published by the
# Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 51
# Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA

from xml.dom.minidom import getDOMImplementation

import kusu.core.database as kusudb

class Status(object):
    def __init__(self, db):
        self._db = db

    def nodegroups(self):
        doc = getDOMImplementation().createDocument(None, "nodegroups", None)
        nodegroups_node = doc.firstChild

        for ng in self._db.NodeGroups.select():
            nodegroup_node = doc.createElement("nodegroup")
            nodegroups_node.appendChild(nodegroup_node)
            add_table_to_parent(doc, nodegroup_node, ng)

        return doc

    def nodes_summary(self):
        node_count = self._db.Nodes.count()

        doc = getDOMImplementation().createDocument(None, "nodes_summary", None)
        nodes_summary_node = doc.firstChild

        node_count_node = doc.createElement("node_count")
        nodes_summary_node.appendChild(node_count_node)

        node_count_text = doc.createTextNode(str(node_count))
        node_count_node.appendChild(node_count_text)

        return doc

def add_table_to_parent(doc, parent, table):
    for col in table.cols:
        col_element = doc.createElement(col)
        table_attribute = table.__getattribute__(col)
        if table_attribute is not None:
            col_data = doc.createTextNode(str(table_attribute))
            col_element.appendChild(col_data)
        parent.appendChild(col_element)
