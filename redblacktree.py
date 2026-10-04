from typing import Optional, Any, Tuple, List
from linkedlist import LinkedList

RED: bool = True
BLACK: bool = False

class RBNode:
    __slots__ = ("key", "parent", "left", "right", "color", "indices_list")
    def __init__(self, key: Any, index: int) -> None:
        self.key: Any = key
        self.parent: Optional[RBNode] = None
        self.left: Optional[RBNode] = None
        self.right: Optional[RBNode] = None
        self.color: bool = RED
        self.indices_list: LinkedList = LinkedList()
        self.indices_list.elem_add(index)

class RedBlackTree:
    def __init__(self) -> None:
        self.root: Optional[RBNode] = None

    def insert(self, key: Any, index: int) -> None:
        current, parent = self.root, None
        while current is not None:
            if key == current.key:
                current.indices_list.elem_add(index)
                return
            parent = current
            current = current.left if key < current.key else current.right

        new_node = RBNode(key, index)
        new_node.parent = parent
        if parent is None:
            self.root = new_node
        elif key < parent.key:
            parent.left = new_node
        else:
            parent.right = new_node
        self._fix_insertion(new_node)

    def search(self, key: Any) -> Tuple[Optional[RBNode], int]:
        current, steps = self.root, 0
        while current is not None:
            steps += 1
            if key == current.key:
                return current, steps
            current = current.left if key < current.key else current.right
        return None, steps

    def delete(self, key: Any) -> None:
        z, _ = self.search(key)
        if z is None: return
        y = z
        y_original_color = y.color
        x: Optional[RBNode] = None
        x_parent: Optional[RBNode] = None

        if z.left is None:
            x = z.right
            x_parent = z.parent
            self._transplant(z, z.right)
        elif z.right is None:
            x = z.left
            x_parent = z.parent
            self._transplant(z, z.left)
        else:
            y = self._maximum(z.left)
            y_original_color = y.color
            x = y.left
            if y.parent == z:
                x_parent = y
            else:
                x_parent = y.parent
                self._transplant(y, y.left)
                y.left = z.left
                if y.left: y.left.parent = y
            self._transplant(z, y)
            y.right = z.right
            if y.right is not None:
                y.right.parent = y
            y.color = z.color
        
        if y_original_color == BLACK:
            self._fix_deletion(x, x_parent)

    def remove_one_log_index(self, key: Any, index: int) -> None:
        node, _ = self.search(key)
        if node:
            node.indices_list.elem_remove(index)
            if node.indices_list.head is None:
                self.delete(key)

    def get_logs_in_range(self, start_key: Any, end_key: Any) -> List[int]:
        result_indices: List[int] = []
        def _in_order(node: Optional[RBNode]) -> None:
            if node is None: return
            if start_key < node.key:
                _in_order(node.left)
            if start_key <= node.key <= end_key:
                result_indices.extend(node.indices_list)
            if node.key < end_key:
                _in_order(node.right)
        _in_order(self.root)
        return result_indices

    def _fix_insertion(self, k: RBNode) -> None:
        while k != self.root and k.parent and k.parent.color == RED:
            if k.parent == k.parent.parent.left:
                u = k.parent.parent.right
                if u and u.color == RED:
                    k.parent.color = BLACK
                    u.color = BLACK
                    k.parent.parent.color = RED
                    k = k.parent.parent
                else:
                    if k == k.parent.right:
                        k = k.parent
                        self._left_rotate(k)
                    k.parent.color = BLACK
                    k.parent.parent.color = RED
                    self._right_rotate(k.parent.parent)
            else:
                u = k.parent.parent.left
                if u and u.color == RED:
                    u.color = BLACK
                    k.parent.color = BLACK
                    k.parent.parent.color = RED
                    k = k.parent.parent
                else:
                    if k == k.parent.left:
                        k = k.parent
                        self._right_rotate(k)
                    k.parent.color = BLACK
                    k.parent.parent.color = RED
                    self._left_rotate(k.parent.parent)
        if self.root: self.root.color = BLACK

    def _fix_deletion(self, x: Optional[RBNode], x_parent: Optional[RBNode]) -> None:
        while x != self.root and (x is None or x.color == BLACK):
            if x_parent is None: break
            if x == x_parent.left:
                s = x_parent.right
                if s and s.color == RED:
                    s.color = BLACK
                    x_parent.color = RED
                    self._left_rotate(x_parent)
                    s = x_parent.right
                if s is None or ((s.left is None or s.left.color == BLACK) and 
                                 (s.right is None or s.right.color == BLACK)):
                    if s: s.color = RED
                    x = x_parent
                    x_parent = x.parent
                else:
                    if s.right is None or s.right.color == BLACK:
                        if s.left: s.left.color = BLACK
                        s.color = RED
                        self._right_rotate(s)
                        s = x_parent.right
                    if s: s.color = x_parent.color
                    if s and s.right: s.right.color = BLACK
                    x_parent.color = BLACK
                    self._left_rotate(x_parent)
                    x = self.root
                    x_parent = None
            else:
                s = x_parent.left
                if s and s.color == RED:
                    s.color = BLACK
                    x_parent.color = RED
                    self._right_rotate(x_parent)
                    s = x_parent.left
                if s is None or ((s.right is None or s.right.color == BLACK) and 
                                 (s.left is None or s.left.color == BLACK)):
                    if s: s.color = RED
                    x = x_parent
                    x_parent = x.parent
                else:
                    if s.left is None or s.left.color == BLACK:
                        if s.right: s.right.color = BLACK
                        s.color = RED
                        self._left_rotate(s)
                        s = x_parent.left
                    if s: s.color = x_parent.color
                    if s and s.left: s.left.color = BLACK
                    x_parent.color = BLACK
                    self._right_rotate(x_parent)
                    x = self.root
                    x_parent = None
        if x: x.color = BLACK

    def _left_rotate(self, x: RBNode) -> None:
        y = x.right
        if not y: return
        x.right = y.left
        if y.left: y.left.parent = x
        y.parent = x.parent
        if not x.parent: self.root = y
        elif x == x.parent.left: x.parent.left = y
        else: x.parent.right = y
        y.left = x
        x.parent = y

    def _right_rotate(self, x: RBNode) -> None:
        y = x.left
        if not y: return
        x.left = y.right
        if y.right: y.right.parent = x
        y.parent = x.parent
        if not x.parent: self.root = y
        elif x == x.parent.right: x.parent.right = y
        else: x.parent.left = y
        y.right = x
        x.parent = y

    def _transplant(self, u: RBNode, v: Optional[RBNode]) -> None:
        if not u.parent: self.root = v
        elif u == u.parent.left: u.parent.left = v
        else: u.parent.right = v
        if v: v.parent = u.parent

    def _maximum(self, node: RBNode) -> RBNode:
        while node.right: node = node.right
        return node

    def clear(self) -> None:
        self.root = None

    def get_preorder_debug_string(self) -> str:
        lines: List[str] = []

        def _build(node: Optional[RBNode], indent: str = "", is_last: bool = True, label: str = "ROOT") -> None:
            if not node:
                return

            marker = "└── " if is_last else "├── "
            
            lines.append(f"{indent}{marker}[{label}] {node.key} ({'R' if node.color else 'B'}) {node.indices_list}")

            new_indent = indent + ("    " if is_last else "│   ")

            children_to_draw = []
            if node.left:
                children_to_draw.append((node.left, "L"))
            if node.right:
                children_to_draw.append((node.right, "R"))

            for i, (child, child_label) in enumerate(children_to_draw):
                is_last_child = (i == len(children_to_draw) - 1)
                _build(child, new_indent, is_last_child, child_label)

        if not self.root:
            return "Empty"
        
        _build(self.root)
        return "\n".join(lines)