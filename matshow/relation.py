import abc
from typing import *


class State(abc.ABC):
    '''
    State hold by each Node, a State can be activated one or multiple times, and result in some different actions.
    '''

    def __init__(self):
        self._activate_counter = 0

    def activate(self, *args, **kwargs):
        self._activate(*args, **kwargs)

        self._activate_counter += 1

    @property
    def activated(self):
        return self._activate_counter

    @abc.abstractmethod
    def _activate(self, *args, **kwargs):
        pass


class DefaultState(State):
    '''
    A State do nothing
    '''

    def _activate(self, *args, **kwargs):
        pass


class Node(abc.ABC):
    def __init__(self, state: State = DefaultState()):
        self.relations: List["Relation"] = []
        self.state = state

    @abc.abstractmethod
    def shape(self) -> List[int]:
        raise NotImplemented

    def add_relation(self, relation: "Relation"):
        self.relations.append(relation)

    def activate(self, offset=None):
        '''
        Activate a cell.
        '''
        self.state.activate()
        if self._activate_impl(offset):
            for rel in self.relations:
                if rel.map:
                    for target in rel.map(offset):
                        rel.target.activate(target)
                rel.target.activate()

    def mark(self, offset):
        '''
        Mark a cell is activated.
        '''
        self._mark_impl(offset)

        for rel in self.relations:
            if rel.map:
                for target in rel.map(offset):
                    rel.target.mark(target)

    def deactivate(self, offset):
        self._deactivate_impl(offset)
        for rel in self.relations:
            for target in rel.map(offset):
                rel.target.activate(target)

    @abc.abstractmethod
    def _activate_impl(self, offset) -> bool:
        '''
        Activate implementation, returns a bool to indicate whether to continue activating other nodes connected by Relations.
        '''
        return True

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

    def __init__(self, source: Node, target: Node):
        self.source = source
        self.target = target
        self.map: Callable[[int], [int]] = None

    def set_map(self, fn: Callable[[int], List[int]]) -> None:
        '''
        Given an offset i, return a list of offsets it maps to.
        '''
        self.map = fn

    def apply(self, i: int) -> List[int]:
        return self.map(i)
