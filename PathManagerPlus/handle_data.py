import uuid
import json
from copy import deepcopy


def get_uuid():
    return uuid.uuid4().hex


def get_data_format(data_type):
    if data_type == 'node':
        node = {
            'name': None,
            'parent_id': None,
            'items': [],
            'sub_nodes': []
        }
        return node
    elif data_type == 'item':
        item = {
            'name': None,
            'path': None,
            'comment': None,
            'parent_id': None
        }
        return item
    else:
        raise TypeError


class JsonDb(dict):

    """A json storage with some functions.

    Usage:

        >>> data = {
            'Jan': 'January',
            'Feb': 'February'
        }
        >>> months = JsonDb(data)
        >>> months
        {"Jan": "January", "Feb": "February"}
        >>> months.pretty_print()
        {
            "Jan": "January",
            "Feb": "February"
        }
        >>> type(months)
        <class '__main__.JsonDb'>
        >>> months.to_json('output.json')
        >>> months2 = JsonDb.from_json('output.json')
        >>> months2
        {"Jan": "January", "Feb": "February"}
        >>> months == months2
        True
    """

    @classmethod
    def from_json(cls, file):
        with open(file, 'r', encoding='utf-8')as fl:
            return cls(json.load(fl))

    @classmethod
    def from_string(cls, json_str):
        return cls(json.loads(json_str))

    def format_json(self):
        return json.dumps(self, indent=4, ensure_ascii=False)

    def pretty_print(self):
        print(self.format_json())

    def to_json(self, file):
        with open(file, 'w', encoding='utf-8')as fl:
            json.dump(self, fl, indent=4, ensure_ascii=False)

    def __str__(self):
        return json.dumps(self, ensure_ascii=False)

    __repr__ = __str__


class DataStorage(dict):

    def __init__(self, data=None):
        if data is None:
            # 初始化数据
            self['nodes'] = {}
            self['items'] = {}
            node = get_data_format('node')
            self['nodes']['root'] = node
        else:
            super().__init__(data)

    @classmethod
    def from_json(cls, file):
        with open(file, encoding='utf-8')as fl:
            data = json.load(fl)
        return cls(data)

    def to_json(self, file, indent=4):
        with open(file, 'w', encoding='utf-8')as fl:
            json.dump(self, fl, indent=indent, ensure_ascii=False)

    def add_item(self, item, parent_id='root'):
        if isinstance(item, dict):
            pass
        elif isinstance(item, str):
            name = item
            item = get_data_format('item')
            item['name'] = name
        else:
            raise TypeError
        while True:
            item_id = get_uuid()
            if item_id not in self['items']:
                break
        item['parent_id'] = parent_id
        self['items'][item_id] = item
        self['nodes'][parent_id]['items'].append(item_id)
        return item_id

    def remove_item(self, item_id):
        parent_node = self['items'][item_id]['parent_id']
        self['items'].pop(item_id)
        self['nodes'][parent_node]['items'].remove(item_id)

    def update_item(self, item_id, update_data):
        for key in update_data.keys():
            if key not in ('name', 'path', 'comment'):
                raise ValueError
        for key, value in update_data.items():
            self['items'][item_id][key] = value

    def add_node(self, name, parent_id='root'):
        while True:
            node_id = get_uuid()
            if node_id not in self['nodes']:
                break
        node = get_data_format('node')
        node['name'] = name
        node['parent_id'] = parent_id
        self['nodes'][node_id] = node
        self['nodes'][parent_id]['sub_nodes'].append(node_id)
        return node_id

    def remove_node(self, node_id):
        # 需要递归删除，同时需要删除掉该节点上所附带的项
        node = self['nodes'][node_id]
        parent_id = node['parent_id']
        sub_nodes = node['sub_nodes']
        for sub_node in sub_nodes:
            self.remove_node(sub_node)
        if parent_id is not None:
            self['nodes'][parent_id]['sub_nodes'].remove(node_id)
        for item_id in node['items']:
            self['items'].pop(item_id)
        self['nodes'].pop(node_id)

    def move_item_within_node(self, item_id, to_index):
        """
        item_id 在 node 的 items 列表里面是唯一的。
        to_index: 0 表示插入到最前面。该值可以是负数，表现和
        python 的 list.insert 本质相同。但在实际使用容易误解。
        比如当该值是 -1 时，代表在最后一个之前插入数值，也就是
        插入值之后的最终结果是在倒数第二个。这个需要特别注意。
        """
        node_id = self['items'][item_id]['parent_id']
        self['nodes'][node_id]['items'].remove(item_id)
        self['nodes'][node_id]['items'].insert(to_index, item_id)

    def move_item_to_first(self, item_id):
        self.move_item_within_node(item_id, 0)

    def move_item_to_last(self, item_id):
        node_id = self['items'][item_id]['parent_id']
        self['nodes'][node_id]['items'].remove(item_id)
        self['nodes'][node_id]['items'].append(item_id)

    def move_item_to_node(self, item_id, node_id, to_index=None):
        """移动列表项到别的树节点上
        to_index 如果不设置值的话，就默认移动到末尾。
        """
        old_parent_id = self['items'][item_id]['parent_id']
        self['items'][item_id]['parent_id'] = node_id
        self['nodes'][old_parent_id]['items'].remove(item_id)
        if to_index is None:
            self['nodes'][node_id]['items'].append(item_id)
        else:
            self['nodes'][node_id]['items'].insert(to_index, item_id)

    def change_node_name(self, node_id, name):
        self['nodes'][node_id]['name'] = name

    def change_node_index(self, node_id, new_index):
        """
        Same parent_id, different index.
        """
        parent_id = self['nodes'][node_id]['parent_id']
        self['nodes'][parent_id]['sub_nodes'].remove(node_id)
        self['nodes'][parent_id]['sub_nodes'].insert(new_index, node_id)

    def change_node_parent(self, node_id, new_parent_id, new_index):
        """
        Different parent_id.
        """
        old_parent_id = self['nodes'][node_id]['parent_id']
        self['nodes'][node_id]['parent_id'] = new_parent_id
        self['nodes'][old_parent_id]['sub_nodes'].remove(node_id)
        self['nodes'][new_parent_id]['sub_nodes'].insert(new_index, node_id)

    def get_node_name(self, node_id):
        return self['nodes'][node_id]['name']

    def get_sub_nodes_name(self, node_id):
        names = []
        for sub_node_id in self['nodes'][node_id]['sub_nodes']:
            names.append(self.get_node_name(sub_node_id))
        return names

    def print_node_name(self, node_id):
        print(self.get_node_name(node_id))

    def print_sub_nodes_name(self, node_id, new_line=True):
        names = self.get_sub_nodes_name(node_id)
        if new_line:
            print('\n'.join(names))
        else:
            print(names)

    def pretty_print(self, indent=4):
        print(json.dumps(self, indent=indent, ensure_ascii=False))

    def check_data_integrity(self):

        # 需要检查
        # 1. 节点的 sub_nodes 含有多余节点
        # 2. 节点的 parent_id 是不存在的，也就是多余的节点，不会被渲染出来的
        # 3. 节点的 parent_id 存在，但是父节点里面的 sub_nodes 没有这个节点
        for node_id, data in self['nodes'].items():
            parent_id = data['parent_id']
            if parent_id is None:
                continue
            # 判断 2
            if parent_id not in self['nodes']:
                return False

            # 判断 3
            if node_id not in self['nodes'][parent_id]['sub_nodes']:
                return False

            # 判断 1
            for sub_node_id in data['sub_nodes']:
                if self['nodes'][sub_node_id]['parent_id'] != node_id:
                    # print(
                    #     f'错误：两个节点的父节点和字节点关系无法对上：' +
                    #     f'{node_id}, {sub_node_id}'
                    # )
                    return False
        return True

    def fix_data(self, json_file=None):
        # 如果给与了文件名，则会强制保存数据覆盖掉原始文件
        # 以父节点为准修复数据
        copy_data = deepcopy(self)

        for node_id, data in copy_data['nodes'].items():
            node_name = data['name']

            # 处理多出来的字节点
            for sub_node_id in data['sub_nodes']:
                sub_node_data = copy_data['nodes'][sub_node_id]
                sub_node_name = sub_node_data['name']
                if sub_node_data['parent_id'] != node_id:
                    self['nodes'][node_id]['sub_nodes'].remove(sub_node_id)
                    print(f'移除多余的字节点：[{node_name}]-[{sub_node_name}]')

            # 处理父节点没有正确链接字节点
            parent_id = data['parent_id']
            if parent_id is None:
                continue
            if parent_id not in copy_data['nodes']:
                # 挂载的父节点不存在的类型
                self['nodes'].pop(node_id)
                print(f'挂载父节点不存在，删除掉节点：[{node_name}]')
                continue
            parent_data = copy_data['nodes'][parent_id]
            parent_name = parent_data['name']
            if node_id not in parent_data['sub_nodes']:
                self['nodes'][parent_id]['sub_nodes'].append(node_id)
                print(f'给父节点添加缺失的字节点,[{parent_name}]+[{node_name}]')
        del copy_data
        if json_file is not None:
            self.to_json(json_file)


def gen_base_data():
    d = DataStorage()
    node = d.add_node('常规')
    d.add_node('程序', node)
    d.add_node('链接', node)
    d.add_node('其他', node)
    return d


if __name__ == '__main__':
    # d = DataStorage.from_json('data.json')
    # status = d.check_data_integrity()
    # print(status)
    # if not status:
    #     d.fix_data(
    #         'data.json'
    #     )
    # d.pretty_print()
    d = DataStorage()
    node_a = d.add_node('A')
    node_b = d.add_node('B', node_a)
    node_c = d.add_node('C', node_b)
    node_d = d.add_node('D', node_b)
    d.add_item('b1', node_b)
    d.add_item('b2', node_b)
    item1 = d.add_item('c1', node_c)
    item2 = d.add_item('c2', node_c)
    item3 = d.add_item('c3', node_c)
    # d.print_sub_nodes_name(node_b, False)
    d.pretty_print()
    d.move_item_to_node(item2, node_a)
    d.pretty_print()
    # d.change_node_parent(node_d, node_a, 0)
    # d.change_node_index(node_d, 0)
    # d.remove_node(node_a)
    # d.change_node_name(node_a, 'Test')
    # print(d['nodes'][node_c]['items'])
    # d.move_item_within_node(item3, 0)
    # d.move_item_to_last(item1)
    # d.move_item_to_first(item3)
    # print(d['nodes'][node_c]['items'])
    # d = gen_base_data()
    # d.pretty_print()
    # d = DataStorage.from_json('data.json')
    # d.pretty_print()
    # d = DataStorage({1: 10})
    # print(d)
