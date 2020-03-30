#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2020/3/30 14:23
# @File    : TreeNode.py
# @author  : dfkai
# @Software: PyCharm
import json
import os


class Node:
    def __init__(self, title, children=[]):
        self.title = title
        self.children = children

    def __str__(self):
        return self.title

    def get_name(self):
        if self.children:
            data = dict(title=self.title, children=[i for i in self.children])
        else:
            data = dict(title=self.title)
        return data


class TreeNode(object):
    def __init__(self, script_name: str = ""):
        self.script_name = script_name

    def get_node(self, file_path: str, node: Node = None) -> Node:
        if not node:
            node = Node(self.script_name,[])
        for i in os.listdir(file_path):
            if os.path.isdir(os.path.join(file_path, i)):
                if not i.startswith('__'):
                    dir_node = self.get_node(os.path.join(file_path, i), Node(i, []))
                    node.children.append(dir_node.get_name())
            else:
                if i.endswith('.py') and not i.startswith('__'):
                    dir_node = Node(i, [])
                    node.children.append(dir_node.get_name())
        return node


if __name__ == '__main__':
    tree_node = TreeNode('脚本文件')
    node = tree_node.get_node(r'C:\Users\libai\dfk-common\日常\scheduler_item\app\schedudler_script')

    print(json.dumps(node.get_name(), indent=4))
