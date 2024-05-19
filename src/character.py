import sys


from pydantic import BaseModel


# An attribute is a characters stats typically.
# Primarily used for Strength, Constitution, Wisdom
# but can be used for skills and saves too
class Attribute(BaseModel):
    name: str
    alias: str
    roll: str
    stat: float


# A counter is a resource that tracks incrementally.
# Starts at 0 typically, and goes up. Can be used for
# tracking bardic inspiration or "spells cast"
class Counter(BaseModel):
    name: str
    alias: str
    value: int
    change: int = 1
    auto_reset: bool = True

    def reset(self):
        if self.auto_reset:
            self.value = 0


# Resources are counters but only decrement on use.
# This can be used to track spell slots or mana points
class Resource(BaseModel):
    name: str
    alias: str
    value: int
    max: int
    change: int = 1
    previous_value: int = -1
    auto_reset: bool = True

    def use(self):
        self.previous_value = self.value
        self.value = self.value - self.change
        return self.value

    def set(self, value: int):
        self.previous_value = self.value
        self.value = value
        return self.value

    def undo(self):
        if self.previous_value != -1:
            self.value = self.previous_value
            self.previous_value = -1

    def reset(self):
        if self.auto_reset:
            self.value = self.max


class CharacterData(BaseModel):
    name: str = ""
    species: str = ""
    age: int = 0
    health: int = 0
    max_health: int = 0
    armor: int = 0


class Character(BaseModel):
    extra_data: dict = {}
    base_data: CharacterData = CharacterData()
    attributes: list[Attribute] = []
    resources: list[Resource] = []
    counters: list[Counter] = []

    def reset(self):
        for res in self.resources:
            res.reset()

        for counter in self.counters:
            counter.reset()

    def add_attr(self, attr: Attribute):
        self.attributes.append(attr)

    def add_resource(self, res: Resource):
        self.resources.append(res)

    def use(self, alias: str):
        for ele in self.resources:
            if alias in ele.alias:
                return ele.use()

    def damage(self, damage: int):
        previous_health = self.base_data.health
        health = previous_health - damage
        if self.base_data.max_health > 0:
            if health > self.base_data.max_health:
                health = self.base_data.max_health
        self.base_data.health = health
        return previous_health, health

    def update(self, alias, attr, value):
        for ele in self.resources:
            if alias in ele.alias:
                try:
                    if getattr(ele, attr) is not None:
                        setattr(ele, attr, value)
                        return ele
                except AttributeError:
                    continue
        for ele in self.counters:
            if alias in ele.alias:
                try:
                    if getattr(ele, attr) is not None:
                        setattr(ele, attr, value)
                        return ele
                except AttributeError:
                    continue
        for ele in self.attributes:
            if alias in ele.alias:
                try:
                    if getattr(ele, attr) is not None:
                        setattr(ele, attr, value)
                        return ele
                except AttributeError:
                    continue

    def update_base(self, alias, value):
        self.base_data.__setattr__(alias, value)
        return self.base_data

    def get(self, alias: str):
        for ele in self.resources:
            if alias in ele.alias:
                return ele
        for ele in self.counters:
            if alias in ele.alias:
                return ele
        for ele in self.attributes:
            if alias in ele.alias:
                return ele

        for key, value in self.extra_data.items():
            if alias in key:
                return value

        return None

    def _check_aliases(self, alias: str):
        for attr in self.attrs:
            if attr.alias == alias:
                return False

        for res in self.resources:
            if res.alias == alias:
                return False

        return True
