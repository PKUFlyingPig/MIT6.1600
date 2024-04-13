from common import H_empty, H_kv, H_internal, traversal_path, Proof

class Traversal:
    def __init__(self, path):
        self._siblings = []
        self._path = path
        self._cur_depth = 0

    def next_direction(self):
        left_or_right = self._path[self._cur_depth]
        self._cur_depth += 1
        return left_or_right

    def sibling(self, n):
        self._siblings.append(n)

    def get_siblings(self):
        return self._siblings

class Node:
    def __init__(self, hashval):
        self._hashval = hashval

    def hashval(self):
        return self._hashval

class EmptyNode(Node):
    def __init__(self):
        super().__init__(H_empty())

    def traverse(self, traversal):
        return traversal.leaf(self)

class KeyValueNode(Node):
    def __init__(self, key, val):
        self._key = key
        self._val = val
        h = H_kv(self._key, self._val)
        super().__init__(h)

    def key(self):
        return self._key

    def val(self):
        return self._val

    def traverse(self, traversal):
        return traversal.leaf(self)

class InternalNode(Node):
    def __init__(self, children):
        assert(len(children) == 2)
        self._children = children
        h = H_internal([c.hashval() for c in self._children])
        super().__init__(h)

    def traverse(self, traversal):
        children = [c for c in self._children]
        leaf_direction = traversal.next_direction()
        traversal.sibling(children[int(not leaf_direction)])
        children[int(leaf_direction)] = children[int(leaf_direction)].traverse(traversal)
        return InternalNode(children)

def node_proof(leaf, siblings):
    if isinstance(leaf, EmptyNode):
        key = None
        val = None
    else:
        key = leaf.key()
        val = leaf.val()
    return Proof(key, val, [s.hashval() for s in siblings])

class LookupTraversal(Traversal):
    def __init__(self, key):
        super().__init__(traversal_path(key))
        self._leaf = None

    def leaf(self, n):
        self._leaf = n
        return n

    def proof(self):
        return node_proof(self._leaf, self._siblings)

class InsertTraversal(Traversal):
    def __init__(self, key, val):
        super().__init__(traversal_path(key))
        self._key = key
        self._val = val
        self._proof = None

    def leaf(self, n):
        if self._proof is None:
            self._proof = node_proof(n, self._siblings)

        if isinstance(n, EmptyNode) or n.key() == self._key:
            return KeyValueNode(self._key, self._val)

        ## Create an internal node, and keep traversing.
        children = [EmptyNode(), EmptyNode()]
        existing_path = traversal_path(n.key())
        children[int(existing_path[self._cur_depth])] = n
        return InternalNode(children).traverse(self)

    def proof(self):
        return self._proof

class Store:
    def __init__(self):
        self.root = EmptyNode()

    def lookup(self, key):
        t = LookupTraversal(key)
        self.root = self.root.traverse(t)
        return t.proof()

    def insert(self, key, val):
        t = InsertTraversal(key, val)
        self.root = self.root.traverse(t)
        return t.proof()

    def reset(self):
        self.root = EmptyNode()
