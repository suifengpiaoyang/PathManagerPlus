import uuid
import json


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

    def change_node_name(self, node_id, name):
        self['nodes'][node_id]['name'] = name

    def pretty_print(self, indent=4):
        print(json.dumps(self, indent=indent, ensure_ascii=False))


def gen_base_data():
    d = DataStorage()
    node = d.add_node('常规')
    d.add_node('文件', node)
    d.add_node('文件夹', node)
    d.add_node('程序', node)
    d.add_node('链接', node)
    return d


if __name__ == '__main__':
    d = DataStorage()
    node_a = d.add_node('A')
    node_b = d.add_node('B', node_a)
    node_c = d.add_node('C', node_b)
    d.add_item('b1', node_b)
    d.add_item('b2', node_b)
    d.add_item('c1', node_c)
    d.add_item('c2', node_c)
    # d.remove_node(node_a)
    d.change_node_name(node_a, 'Test')
    d.pretty_print()
    # d = gen_base_data()
    # d.pretty_print()
    # d = DataStorage.from_json('data.json')
    # d.pretty_print()
    # d = DataStorage({1: 10})
    # print(d)
