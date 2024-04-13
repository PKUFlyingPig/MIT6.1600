from common import H_empty, H_kv, H_internal, traversal_path, Proof

class Client:
    def __init__(self, store, root_hash = H_empty()):
        self._store = store
        self._root_hash = root_hash
        self.verbose_validate = False

    def validate(self, path_key, proof):
        assert(type(proof) == Proof)
        assert(proof.key == None or type(proof.key) == bytes)
        assert(proof.val == None or type(proof.val) == bytes)
        assert(type(proof.siblings) == list and all([type(s) == bytes for s in proof.siblings]))

        if proof.key is None and proof.val is None:
            node_hash = H_empty()
        else:
            node_hash = H_kv(proof.key, proof.val)

        if self.verbose_validate:
            print("Proof of subtree: key=%s, val=%s, node_hash=%s" % (proof.key, proof.val, node_hash))

        path = traversal_path(path_key)
        for (leaf_direction, sibling) in reversed(list(zip(path, proof.siblings))):
            children = [None, None]
            children[int(leaf_direction)] = node_hash
            children[int(not leaf_direction)] = sibling
            node_hash = H_internal(children)
            if self.verbose_validate:
                print("Traversal path for", path_key, "is", ("right" if leaf_direction else "left"))
                print(("Right" if not leaf_direction else "Left"), "sibling hash from proof is", sibling)
                print("Computed subtree hash:", node_hash)

        if self.verbose_validate:
            print("Computed root_hash from proof:", node_hash)
            print("Expected root_hash from client:", self._root_hash)

        if self._root_hash != node_hash:
            raise Exception("Root hash mismatch")

    def lookup(self, key):
        proof = self._store.lookup(key)
        self.validate(key, proof)

        ## If we found the key, return it; otherwise (empty or other key), None
        if proof.key == key:
            return proof.val
        else:
            return None

    def insert(self, key, val):
        proof = self._store.insert(key, val)
        self.validate(key, proof)

        new_hash = H_kv(key, val)
        path = traversal_path(key)

        if proof.key is not None and proof.key != key:
            old_path = traversal_path(proof.key)

            match_depth = 0
            while path[match_depth] == old_path[match_depth]:
                match_depth += 1
            fork_depth = match_depth + 1

            old_sibling = H_kv(proof.key, proof.val)
            for leaf_direction in reversed(path[len(proof.siblings):fork_depth]):
                children = [None, None]
                children[int(leaf_direction)] = new_hash
                children[int(not leaf_direction)] = old_sibling
                new_hash = H_internal(children)
                old_sibling = H_empty()

        for (leaf_direction, sibling) in reversed(list(zip(path, proof.siblings))):
            children = [None, None]
            children[int(leaf_direction)] = new_hash
            children[int(not leaf_direction)] = sibling
            new_hash = H_internal(children)

        self._root_hash = new_hash

    def reset(self):
        self._store.reset()
        self._root_hash = H_empty()
