from enum import Enum
from typing import NamedTuple, Optional, Any, Generator

class Status(Enum):
    EMPTY = 0
    OCCUPIED = 1
    DELETED = 2

class Entry:
    __slots__ = ("key", "value", "status")

    def __init__(self) -> None:
        self.key: Optional[Any] = None
        self.value: Optional[Any] = None
        self.status: Status = Status.EMPTY

class SearchResult(NamedTuple):
    value: Optional[Any]
    steps: int

class HashMap:
    MIN_CAPACITY: int = 10
    LOAD_FACTOR: float = 0.75
    MIN_FACTOR: float = 0.2

    def __init__(self, initial_capacity: int = 17) -> None:
        self.capacity: int = max(initial_capacity, self.MIN_CAPACITY)
        self.table: list[Entry] = [Entry() for _ in range(self.capacity)]
        self.size: int = 0
        self.c1: int = 1
        self.c2: int = 1

    def _custom_hash(self, key: Any) -> int:
        return sum(ord(char) for char in str(key))

    def _hash1(self, key: Any) -> int:
        return abs(self._custom_hash(key)) % self.capacity

    def _quadratic_offset(self, i: int) -> int:
        return self.c1 * i + self.c2 * i * i

    def _probe_sequence(self, key: Any) -> Generator[int, None, None]:
        h1 = self._hash1(key)
        for i in range(self.capacity):
            yield (h1 + self._quadratic_offset(i)) % self.capacity

    def _resolve_collision(self, key: Any, for_insertion: bool) -> int:
        deleted_index: int = -1
        for index in self._probe_sequence(key):
            entry = self.table[index]

            if entry.status is Status.EMPTY:
                return deleted_index if (for_insertion and deleted_index != -1) else index
            if entry.status is Status.DELETED:
                if for_insertion and deleted_index == -1:
                    deleted_index = index
            elif entry.key == key:  
                return index

        return deleted_index

    def _upsize(self) -> None:
        if (self.size + 1) / self.capacity > self.LOAD_FACTOR:
            self._resize(self.capacity * 2)

    def _downsize(self) -> None:
        while self.capacity > self.MIN_CAPACITY and (self.size / self.capacity) < self.MIN_FACTOR:
            new_capacity = max(self.capacity // 2, self.MIN_CAPACITY)

            if new_capacity >= self.capacity:
                break
                
            self._resize(new_capacity)

    def _resize(self, new_capacity: int) -> None:
        old_table = self.table
        self.capacity = new_capacity
        self.table = [Entry() for _ in range(self.capacity)]
        self.size = 0
        
        for entry in old_table:
            if entry.status is Status.OCCUPIED:
                index = self._resolve_collision(entry.key, True)
                
                new_entry = self.table[index]
                new_entry.key = entry.key
                new_entry.value = entry.value
                new_entry.status = Status.OCCUPIED
                self.size += 1

    def insert(self, key: Any, array_index: int) -> bool:
        existing = self._resolve_collision(key, False)
        if existing != -1 and self.table[existing].status is Status.OCCUPIED:
            return False

        self._upsize()
        
        index = self._resolve_collision(key, True)
        if index == -1:
            self._resize(self.capacity * 2 + 1)
            index = self._resolve_collision(key, True)

        entry = self.table[index]
        entry.key, entry.value, entry.status = key, array_index, Status.OCCUPIED
        self.size += 1
        return True
    
    def update_value(self, key: Any, new_array_index: int) -> bool:
        index = self._resolve_collision(key, False)
        if index != -1 and self.table[index].status is Status.OCCUPIED:
            self.table[index].value = new_array_index
            return True
        return False

    def delete(self, key: Any) -> int:
        index = self._resolve_collision(key, False)
        entry = self.table[index] if index != -1 else None
        if entry is None or entry.status is not Status.OCCUPIED:
            return -1

        target_value = entry.value
        entry.key, entry.value, entry.status = None, None, Status.DELETED
        self.size -= 1
        
        self._downsize()
        return target_value if target_value is not None else -1

    def search(self, key: Any) -> SearchResult:
        steps: int = 0
        for steps, index in enumerate(self._probe_sequence(key), start=1):
            entry = self.table[index]
            if entry.status is Status.EMPTY:
                break
            if entry.status is Status.OCCUPIED and entry.key == key:
                return SearchResult(entry.value, steps)
        else:
            steps = self.capacity
        return SearchResult(None, steps)

    def print_debug(self) -> str:
        lines: list[str] = ["Index | Status | Key -> Value | [Primary Hash (h1)] -> Probe Sequence"]
        
        for i, entry in enumerate(self.table):
            if entry.status is Status.OCCUPIED:
                h1 = self._hash1(entry.key)
                
                if h1 != i:
                    probe_seq: list[str] = []
                    for step, idx in enumerate(self._probe_sequence(entry.key)):
                        probe_seq.append(f"p{step}:{idx}")
                        if idx == i:
                            break
                    collision_info = f" | Collision h1={h1} -> Sequence: {' -> '.join(probe_seq)}"
                else:
                    collision_info = f" | No Collision (h1={h1})"

                lines.append(f"{i:02d} | 1 (OCCUPIED) | {entry.key} -> ArrayIdx: {entry.value}{collision_info}")
                
            elif entry.status is Status.DELETED:
                lines.append(f"{i:02d} | 2 (DELETED)  | -")
            else:
                lines.append(f"{i:02d} | 0 (EMPTY)    | -")
                
        return "\n".join(lines)