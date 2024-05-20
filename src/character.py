from datetime import datetime
import sys
import re
import itertools

from pydantic import BaseModel
import src.extras as extras


# An attribute is a characters stats typically.
# Primarily used for Strength, Constitution, Wisdom
# but can be used for skills and saves too
class Attribute(BaseModel):
    name: str
    alias: str
    roll: str
    stat: int
    mod: int = 0


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


class Quest(BaseModel):
    name: str = ""
    giver: str = ""
    objective: str = ""
    due: str | int = ""
    outcome: str = ""


class Note(BaseModel):
    name: str
    date: datetime = datetime.today()
    note: str = ""


class Ability(BaseModel):
    name: str
    alias: str
    roll: str
    type: str


class Character(BaseModel):
    extra_data: dict = {}
    base_data: CharacterData = CharacterData()
    attributes: list[Attribute] = []
    resources: list[Resource] = []
    counters: list[Counter] = []
    quests: list[Quest] = []
    notes: list[Note] = []
    abilities: list[Ability] = []

    def note_append(self, name, value):
        for note in self.notes:
            if note.name == name:
                note.note = note.note + "\n\n" + value
                return note

    def note_get(self, name):
        for note in self.notes:
            if note.name == name:
                return note

    def note_delete(self, name):
        remove_index = -1
        for index, note in enumerate(self.notes):
            if note.name == name:
                remove_index = index

        if remove_index > -1:
            self.notes.pop(remove_index)
            return True
        return False

    def note_select(self, name):
        for note in self.notes:
            if note.name == name:
                return note

        return None

    def note_new(self, note: Note):
        self.notes.append(note)
        return note

    def note_mode(self, new_note: Note):
        if len(self.notes) > 0:
            for note in self.notes:
                if note.name == new_note.name:
                    note = new_note
                    return "Note found and replaced"
        else:
            self.notes.append(new_note)
            print(self.notes)
            return "New note created on character"

    def quest_update(self, name, attr, value):
        for quest in self.quests:
            if name in quest.name:
                setattr(quest, attr, value)
                return quest

    def quest_new(self, quest: Quest):
        self.quests.append(quest)
        return quest

    def ability_roll(self, alias):
        pattern = "((?>@)([0-9a-zA-Z]+).([0-9a-zA-Z]+))"

        for ability in self.abilities:
            if ability.alias == alias or ability.name == alias:
                roll_str = ability.roll
                matches = re.findall(pattern, ability.roll)
                if len(matches) > 0:
                    for match in matches:
                        full_match = match[0]
                        roll_alias = match[1]
                        roll_stat = match[2]
                        print(roll_alias)
                        print(roll_stat)

                        roll_data = self.get_roll_data(roll_alias, roll_stat)
                        print(roll_data)

                        roll_str = roll_str.replace(full_match, roll_data)

                print(roll_str)
                result = roll(roll_str)

                return result

    def get_roll_data(self, roll_str):
        pattern = "((?>@)([0-9a-zA-Z]+).([0-9a-zA-Z]+))"
        matches = re.findall(pattern, roll_str)
        if len(matches) > 0:
            for match in matches:
                full_match = match[0]
                roll_alias = match[1]
                roll_stat = match[2]

                lists = [self.abilities, self.attributes, self.resources, self.counters]
                all = itertools.chain(*lists)

                roll_data = 0
                for ele in all:
                    if ele.alias and ele.alias == roll_alias:
                        try:
                            roll_data = getattr(ele, roll_stat)
                        except AttributeError:
                            pass

                print(roll_data)

                roll_out, _ = extras.roll(str(roll_data))
                print(roll_out)
                roll_str = roll_str.replace(full_match, str(roll_out))

        return roll_str

    def ability_update(self, name, attr, value):
        for ability in self.abilities:
            if name in ability.name:
                setattr(ability, attr, value)
                return ability

    def ability_new(self, ability: Ability):
        self.abilities.append(ability)
        return ability

    def reset(self):
        for res in self.resources:
            res.reset()

        for counter in self.counters:
            counter.reset()

    def attribute_add(self, attr: Attribute):
        self.attributes.append(attr)

    def resource_add(self, res: Resource):
        self.resources.append(res)

    def counter_add(self, cou: Counter):
        self.counters.append(cou)

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
        lists = [self.abilities, self.attributes, self.resources, self.counters]
        all = itertools.chain(*lists)

        for ele in all:
            if ele.alias and ele.alias == alias:
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
        lists = [self.abilities, self.attributes, self.resources, self.counters]
        all = itertools.chain(*lists)

        for ele in all:
            if ele.alias and ele.alias == alias:
                return ele

        for key, value in self.extra_data.items():
            if alias in key:
                return value

        return None

    def _check_aliases(self, alias: str):
        lists = [self.abilities, self.attributes, self.resources, self.counters]
        all = itertools.chain(*lists)

        for ele in all:
            if ele.alias and ele.alias == alias:
                return False

        return True
