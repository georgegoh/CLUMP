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

try:
    set
except NameError:
    from sets import Set as set

import kusu.core.database as kusudb
from kusu.shell import Status

# NOTE:
# The code below can be a bit confusing because the term 'node' is overloaded.
# It can mean both a node in the cluster as well as a node in the XML DOM. Be
# careful!
class TestStatus(object):
    def test_nodegroups(self):
        db = kusudb.DB('sqlite', ':memory:')
        db.bootstrap()

        status = Status(db)
        nodegroups_xml = status.nodegroups()

        expected_ngname_set = set(["installer", "compute", "unmanaged"])
        ngname_nodes = nodegroups_xml.getElementsByTagName("ngname")
        ngname_set = set([ngname.firstChild.nodeValue for ngname in ngname_nodes])

        assert status._db == db, "Setting status._db failed"
        assert expected_ngname_set == ngname_set, \
                "XML document contains the following nodes: %s, expected: %s" % (ngname_set, expected_ngname_set)

        expected_column_set = set(db.NodeGroups.cols)
        for ng in nodegroups_xml.getElementsByTagName("nodegroup"):
            ngname_nodes = ng.getElementsByTagName("ngname")
            assert len(ngname_nodes) == 1, "More than 1 'ngname' node in nodegroup"

            ngname = ngname_nodes[0].firstChild.nodeValue
            column_set = set([n.tagName for n in ng.childNodes])
            assert expected_column_set == column_set, \
                    "Nodegroup '%s' in XML document contains the following columns: %s, expected: %s" % (ngname, column_set, expected_column_set)

    def test_nodes_summary(self):
        db = kusudb.DB('sqlite', ':memory:')
        db.bootstrap()

        status = Status(db)
        nodes_summary_xml = status.nodes_summary()

        expected_node_count = '1'
        node_count_nodes = nodes_summary_xml.getElementsByTagName("node_count")
        assert len(node_count_nodes) == 1, "More than 1 'node_count' node in nodes summary"

        node_count = node_count_nodes[0].firstChild.nodeValue

        assert expected_node_count == node_count, "Node summary reports %s nodes, expected %s" % (node_count, expected_node_count)

        db.Nodes(name='test-00', ngid=1).flush()
        db.Nodes(name='test-01', ngid=1).flush()

        nodes_summary_xml = status.nodes_summary()

        expected_node_count = '3'
        node_count_nodes = nodes_summary_xml.getElementsByTagName("node_count")
        assert len(node_count_nodes) == 1, "More than 1 'node_count' node in nodes summary"

        node_count = node_count_nodes[0].firstChild.nodeValue

        assert expected_node_count == node_count, "Node summary reports %s nodes, expected %s" % (node_count, expected_node_count)
