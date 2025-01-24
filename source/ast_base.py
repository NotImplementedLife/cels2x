class ASTNode:
    def __init__(self):
        self.__parent = None
        self.__parent_key = None
        self.__children = {}
        self.properties = {}

    def register_child_key(self, key):
        self.__children[key] = None

    def register_children_list_key(self, key):
        self.__children[key] = []

    def get_parent(self): return self.__parent

    def set_parent(self, parent, key):
        if self.__parent==parent and self.__parent_key==key: return

        if self.__parent is not None: self.__parent.__remove_child(self)
        if parent is None: return

        if not key in parent.__children:
            raise RuntimeError(f"Node child key not found: `{key}`")
        if isinstance(parent.__children[key], list):
            parent.__children[key].append(self)
        else:
            if parent.__children[key] is not None:
                parent.__remove_child(parent.__children[key])
            parent.__children[key] = self
        self.__parent = parent
        self.__parent_key = key

    def __contains_child(self, node):
        if node.__parent!=self: return False
        pk = node.__parent_key
        if not pk in self.__children: return False
        if isinstance(self.__children[pk], list):
            return node in self.__children[pk]
        return self.__children[pk]==node

    def __remove_child(self, node):
        if node.__parent!=self:
            raise RuntimeError("Node can only be removed by its own parent")
        pk = node.__parent_key
        if not pk in self.__children:
            raise RuntimeError(f"Node child key not found: `{pk}`")
        if isinstance(self.__children[pk], list):
            index = self.__children[pk].index(node)
            self.__children[pk].pop(index)
            #self.__children[pk].remove(node)
        else:
            self.__children[pk] = None
        node.__parent = None
        node.__parent_key = None

    parent = property(get_parent)

    def _get_children_by_key(self, key): return self.__children[key]

    @staticmethod
    def simple_child_getter(key):
        def f(obj): return obj._get_children_by_key(key)
        return f

    @staticmethod
    def simple_child_setter(key):
        def f(obj, node):
            if node is not None:
                node.set_parent(obj, key)
            else:
                if isinstance(obj.__children[key], list):
                    raise RuntimeError("Could not set a list of children to None")
                obj.__children[key] = None
        return f

    def simple_children_list_getter(key):
        def f(obj): return obj._get_children_by_key(key)
        return f

    def enumerate_children(self):
        for v in self.__children.values():
            if isinstance(v, list):
                for n in v:
                    yield n
            elif v is not None:
                assert isinstance(v, ASTNode)
                yield v

    def enumerate_children_deep(self):
        for v in self.__children.values():
            if isinstance(v, list):
                for n in v:
                    yield n
                    for c in n.enumerate_children_deep(): yield c
            elif v is not None:
                assert isinstance(v, ASTNode)
                yield v
                for c in v.enumerate_children_deep(): yield c

    def parse(self, func):
        if not func(self):
            for v in self.__children.values():
                if isinstance(v, list):
                    for n in v:
                        n.parse(func)
                elif v is not None:
                    assert isinstance(v, ASTNode)
                    v.parse(func)

    def debug(self):
        print(self.__children)

    def clone(self):
        raise NotImplementedError(f"clone {type(self).__name__}")

    def insert_before_it(self, node):
        print(type(self))
        print(type(self.parent))
        if not isinstance(self.parent, ASTBlock):
            raise RuntimeError("Cannot use insert_before unless parent of the node is an ASTBlock")
        block = self.parent
        node.set_parent(block, "children")
        node = block.children[-1]
        block.children.pop()
        ix = block.children.index(self)
        block.children.insert(ix, node)

    def replace_with(self, node):
        assert isinstance(node, ASTNode)
        parent = self.__parent
        pkey = self.__parent_key
        if isinstance(parent.__children[pkey], list):
            for i, n in enumerate(parent.__children[pkey]):
                if n is self:
                    node.__parent = parent
                    node.__parent_key = pkey
                    parent.__children[pkey][i] = node
                    self.__parent = None
                    self.__parent_key = None
                    return
        else:
            assert parent.__children[pkey] is self
            node.__parent = parent
            node.__parent_key = pkey
            parent.__children[pkey] = node
            self.__parent = None
            self.__parent_key = None
            return

    def with_all(self, node_type, action):
        def f(node):
            if isinstance(node, node_type):
                action(node)
        self.parse(f)

class ASTBlock(ASTNode):
    children = property(ASTNode.simple_children_list_getter("children"))

    def __init__(self, *children):
        super(ASTBlock, self).__init__()
        self.register_children_list_key("children")
        children = self.__flatten_blocks(children)
        for child in children:
            assert isinstance(child, ASTNode), f"Expected ASTNode, found {type(child)}"
            child.set_parent(self, "children")

    def __flatten_blocks(self, children:list[ASTNode]):
        result = []
        for c in children:
            if isinstance(c, type(self)):
                rnodes = self.__flatten_blocks(c.children)
                result+=rnodes
            else:
                result.append(c)
        return result

    def insert_at_end(self, node):
        node.set_parent(self, "children")

    def __str__(self):
        return f"[Block({len(self.children)})]\n"+";\n".join(map(str, self.children))

class ASTSimpleInstruction(ASTNode):
    name = property(lambda s:s.__name)

    def __init__(self, name:str):
        super(ASTSimpleInstruction, self).__init__()
        assert isinstance(name, str)
        self.__name=name

    def __str__(self): return self.__name