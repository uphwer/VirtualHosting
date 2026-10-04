from typing import Optional, Any, Iterator

class Node:
    __slots__ = ("data", "next", "prev")

    def __init__(self, data: Any) -> None:
        self.data: Any = data
        self.next: Optional[Node] = None
        self.prev: Optional[Node] = None


class LinkedList:
    def __init__(self) -> None:
        self.head: Optional[Node] = None

    def __iter__(self) -> Iterator[Any]:
        node = self.head
        while node is not None:
            yield node.data
            node = node.next

    def __str__(self) -> str:
        return " ".join(str(value) for value in self) or "List is empty."

    def elem_add(self, data: Any) -> Optional[Node]:
        new_node = Node(data)
        if self.head is None:
            self.head = new_node
            return self.head

        prev_node: Optional[Node] = None
        node: Optional[Node] = self.head
        while node is not None and node.data > data:
            prev_node, node = node, node.next

        new_node.prev = prev_node
        new_node.next = node

        if node is not None:
            node.prev = new_node

        if prev_node is None:
            self.head = new_node
        else:
            prev_node.next = new_node

        return self.head

    def elem_remove(self, value: Any) -> Optional[Node]:
        node = self.head
        while node is not None:
            if node.data == value:
                node = self._unlink(node)
            else:
                node = node.next
        return self.head

    def _unlink(self, node: Node) -> Optional[Node]:
        if node.prev is None:
            self.head = node.next
        else:
            node.prev.next = node.next
        if node.next is not None:
            node.next.prev = node.prev
        return node.next
