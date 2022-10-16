import abc
from typing import *


class Node(abc.ABC):
    def __init__(self, start: int, end: int):
        self.domain = (start, end)
        self.relations: List["Relation"] = []

    @abc.abstractmethod
    def shape(self) -> List[int]:
        raise NotImplemented

    def add_relation(self, relation: "Relation"):
        self.relations.append(relation)

    def activate(self, offset):
        '''
        Activate a cell.
        '''
        self._activate_impl(offset)

        for rel in self.relations:
            for target in rel.map(offset):
                rel.target.activate(target)

    def mark(self, offset):
        '''
        Mark a cell is activated.
        '''
        self._mark_impl(offset)

        for rel in self.relations:
            for target in rel.map(offset):
                rel.target.mark(target)

    def deactivate(self, offset):
        self._deactivate_impl(offset)
        for rel in self.relations:
            for target in rel.map(offset):
                rel.target.activate(target)

    @abc.abstractmethod
    def _activate_impl(self, offset):
        raise NotImplemented

    @abc.abstractmethod
    def _mark_impl(self, offset):
        raise NotImplemented

    @abc.abstractmethod
    def _deactivate_impl(self, offset):
        raise NotImplemented


class Relation(abc.ABC):
    '''
    Relation indicates the mapping relation between the offset of two Nodes.

    It assumes the offset is continuous, the source Node's offset should map to one or more offsets in the target node.
    '''

    def __init__(self, target: Node):
        self.target = target
        self.map: Callable[[int], [int]] = None

    def set_map(self, fn: Callable[int, int]) -> None:
        '''
        Given an offset i, return a list of offsets it maps to.
        '''
        self.map = fn

    def apply(self, i: int) -> List[int]:
        return self.map(i)
