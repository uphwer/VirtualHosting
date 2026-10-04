import os
import re
from typing import Tuple, List, Optional
from models import Site, Log, CustomDate
from hashmap import HashMap
from redblacktree import RedBlackTree

def parse_date_range(start_text: str, end_text: str) -> Tuple[CustomDate, CustomDate]:
    return CustomDate(start_text), CustomDate(end_text)


def is_valid_domain(domain: str) -> bool:
    pattern = r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$"
    return bool(re.match(pattern, domain))


def is_valid_time_hms(time_str: str) -> bool:
    pattern = r"^(?:[01]\d|2[0-3]):[0-5]\d:[0-5]\d$"
    return bool(re.match(pattern, time_str))


class DataEngine:
    def __init__(self, initial_capacity: int) -> None:
        self.sites_db: HashMap = HashMap(initial_capacity)
        self.logs_db: RedBlackTree = RedBlackTree()
        self.logs_by_date_db: RedBlackTree = RedBlackTree()
        self.sites_array: List[Site] = []
        self.logs_array: List[Log] = []

    def rebuild_logs_trees(self) -> None:
        self.logs_db.clear()
        self.logs_by_date_db.clear()
        for idx, log in enumerate(self.logs_array):
            self.logs_db.insert(log.domain, idx)
            self.logs_by_date_db.insert(log.date, idx)

    def insert_site(self, site: Site) -> None:
        self.sites_array.append(site)
        self.sites_db.insert(site.domain, len(self.sites_array) - 1)

    def _is_duplicate_log(self, log_obj: Log) -> bool:
        node, _ = self.logs_db.search(log_obj.domain)
        if node is None:
            return False
        for idx in node.indices_list:
            existing = self.logs_array[idx]
            if (existing.date == log_obj.date and
                    existing.time == log_obj.time and
                    existing.type == log_obj.type and
                    existing.message == log_obj.message):
                return True
        return False

    def insert_log(self, log_obj: Log) -> None:
        if self._is_duplicate_log(log_obj):
            raise ValueError(f"Duplicate log entry for domain '{log_obj.domain}'")
            
        new_idx = len(self.logs_array)
        self.logs_array.append(log_obj)
        
        self.logs_db.insert(log_obj.domain, new_idx)
        self.logs_by_date_db.insert(log_obj.date, new_idx)

    def remove_log_at_index(self, target_idx: int) -> None:
        if 0 <= target_idx < len(self.logs_array):
            self._remove_log_and_swap_last(target_idx)

    def remove_site_with_logs(self, domain: str) -> None:
        self._remove_site_entry(domain)
        idx = 0
        while idx < len(self.logs_array):
            if self.logs_array[idx].domain == domain:
                self._remove_log_and_swap_last(idx)
            else:
                idx += 1

    def _remove_log_and_swap_last(self, target_idx: int) -> None:
        log_to_remove = self.logs_array[target_idx]
        last_idx = len(self.logs_array) - 1

        self.logs_db.remove_one_log_index(log_to_remove.domain, target_idx)
        self.logs_by_date_db.remove_one_log_index(log_to_remove.date, target_idx)

        if target_idx != last_idx:
            moved_log = self.logs_array[last_idx]
            node_domain, _ = self.logs_db.search(moved_log.domain)
            if node_domain:
                node_domain.indices_list.elem_remove(last_idx)
                node_domain.indices_list.elem_add(target_idx)
            
            node_date, _ = self.logs_by_date_db.search(moved_log.date)
            if node_date:
                node_date.indices_list.elem_remove(last_idx)
                node_date.indices_list.elem_add(target_idx)
                
            
            self.logs_array[target_idx] = moved_log

        self.logs_array.pop()

    def rebuild_date_tree(self) -> None:
        self.logs_by_date_db.clear()
        for idx, log in enumerate(self.logs_array):
            self.logs_by_date_db.insert(log.date, idx)

    def _remove_site_entry(self, domain: str) -> None:
        deleted_idx = self.sites_db.delete(domain)
        if deleted_idx == -1:
            return
        last_idx = len(self.sites_array) - 1
        if deleted_idx == last_idx:
            self.sites_array.pop()
            return
        moved_site = self.sites_array[last_idx]
        self.sites_array[deleted_idx] = moved_site
        self.sites_array.pop()
        self.sites_db.update_value(moved_site.domain, deleted_idx)

    def save_sites_to_file(self, filepath: str) -> None:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("[SITES]\n")
            for site in self.sites_array:
                f.write(f"{site.domain};{site.owner};{site.tariff}\n")

    def save_logs_to_file(self, filepath: str) -> None:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("[LOGS]\n")
            for log in self.logs_array:
                f.write(f"{log.domain};{log.date};{log.time};{log.type};{log.message}\n")

    def load_sites_from_file(self, filepath: str) -> None:
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File {filepath} not found.")

        lines: List[str] = []
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    lines.append(line)

        if not lines or lines[0] != "[SITES]":
            raise ValueError("Invalid file format: missing required header [SITES]")

        old_logs = list(self.logs_array)

        self.sites_array.clear()
        self.sites_db = HashMap(self.sites_db.capacity)

        # 3. Загружаем сайты из файла
        for i, line in enumerate(lines[1:], start=2):
            parts = [p.strip() for p in line.split(";")]
            if len(parts) != 3:
                raise ValueError(f"Error on line {i}: expected 3 fields, got {len(parts)}")
            
            domain, owner, tariff = parts
            if not domain or not owner or not tariff:
                raise ValueError(f"Error on line {i}: entry fields cannot be empty")
            
            if not is_valid_domain(domain):
                raise ValueError(f"Error on line {i}: '{domain}' is not a valid domain")
            
            if self.sites_db.search(domain).value is not None:
                idx = self.sites_db.search(domain).value
                self.sites_array[idx] = Site(domain, owner, tariff)
            else:
                site_obj = Site(domain, owner, tariff)
                self.sites_array.append(site_obj)
                self.sites_db.insert(domain, len(self.sites_array) - 1)

        new_logs_array = []
        for log in old_logs:
            if self.sites_db.search(log.domain).value is not None:
                new_logs_array.append(log)
        
        self.logs_array = new_logs_array
        self.rebuild_logs_trees()

    def load_logs_from_file(self, filepath: str) -> None:
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File {filepath} not found.")

        lines: List[str] = []
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    lines.append(line)

        if not lines or lines[0] != "[LOGS]":
            raise ValueError("Invalid file format: missing required header [LOGS]")

        new_logs_array: List[Log] = []
        
        for i, line in enumerate(lines[1:], start=2):
            parts = [p.strip() for p in line.split(";")]
            if len(parts) != 5:
                raise ValueError(f"Error on line {i}: expected 5 fields, got {len(parts)}")
            
            domain, date_str, time_str, log_type, message = parts
            if not domain or not date_str or not time_str or not log_type or not message:
                raise ValueError(f"Error on line {i}: log fields cannot be empty")

            if not is_valid_domain(domain):
                raise ValueError(f"Error on line {i}: invalid log domain '{domain}'")

            if not is_valid_time_hms(time_str):
                raise ValueError(f"Error on line {i}: invalid time format '{time_str}'.")

            try:
                log_obj = Log(domain, date_str, time_str, log_type, message)
            except ValueError as e:
                raise ValueError(f"Error on line {i} during date parsing: {e}")

            if self.sites_db.search(domain).value is None:
                continue

            for existing in new_logs_array:
                if (existing.domain == log_obj.domain and
                        existing.date == log_obj.date and
                        existing.time == log_obj.time and
                        existing.type == log_obj.type and
                        existing.message == log_obj.message):
                    raise ValueError(f"Error on line {i}: duplicate log entry in file")

            new_logs_array.append(log_obj)

        self.logs_array = new_logs_array
        self.rebuild_logs_trees()