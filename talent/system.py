"""pairwise-talent-system - TalentSystem

MMO 天赋/铭文/配装/属性系统。
"""


class TalentSystem:
    LEVEL_CAP = 60
    ATTRIBUTE_CAP = 9999
    TALENT_POINTS_PER_LEVEL = 1

    ATTRIBUTE_CONVERSION = {
        "strength": {"attack_power": 2.0},
        "agility": {"attack_power": 1.0, "crit_rating": 0.05},
        "intellect": {"spell_power": 2.0, "mana": 10.0},
        "stamina": {"health": 10.0},
    }

    STAT_WEIGHTS = {
        "warrior": {"strength": 1.0, "agility": 0.6, "intellect": 0.0, "stamina": 0.8},
        "mage": {"strength": 0.0, "agility": 0.3, "intellect": 1.0, "stamina": 0.5},
        "rogue": {"strength": 0.5, "agility": 1.0, "intellect": 0.0, "stamina": 0.6},
    }

    TALENT_TREE = {
        "power_strike": {
            "name": "强力打击", "tier": 1, "max_rank": 3,
            "prerequisites": [], "conflicts": [],
            "bonus": {"strength": 5},
        },
        "toughness": {
            "name": "坚韧", "tier": 1, "max_rank": 3,
            "prerequisites": [], "conflicts": [],
            "bonus": {"stamina": 5},
        },
        "blade_flurry": {
            "name": "剑刃乱舞", "tier": 2, "max_rank": 2,
            "prerequisites": ["power_strike"], "conflicts": ["shield_wall"],
            "bonus": {"agility": 8},
        },
        "shield_wall": {
            "name": "盾墙", "tier": 2, "max_rank": 2,
            "prerequisites": ["toughness"], "conflicts": ["blade_flurry"],
            "bonus": {"stamina": 8},
        },
        "titan_wrath": {
            "name": "泰坦之怒", "tier": 3, "max_rank": 1,
            "prerequisites": ["blade_flurry"], "conflicts": [],
            "bonus": {"strength": 15, "attack_power": 30},
        },
    }

    GLYPHS = {
        "glyph_of_power": {
            "name": "力量铭文", "slot": "major", "required_level": 15,
            "effect": {"skill": "power_strike", "bonus": {"attack_power": 20}},
        },
        "glyph_of_swiftness": {
            "name": "迅捷铭文", "slot": "major", "required_level": 30,
            "effect": {"skill": "blade_flurry", "bonus": {"agility": 10}},
        },
        "glyph_of_vitality": {
            "name": "活力铭文", "slot": "minor", "required_level": 10,
            "effect": {"skill": "toughness", "bonus": {"health": 100}},
        },
    }

    GLYPH_SLOT_COUNTS = {"major": 3, "minor": 3}

    SET_BONUSES = {
        "warlord": {2: {"strength": 10}, 4: {"attack_power": 50}},
        "arcanist": {2: {"intellect": 10}, 4: {"spell_power": 50}},
    }

    def __init__(self, hero_class="warrior", level=LEVEL_CAP):
        self.state = {}
        self.hero_class = hero_class if hero_class in self.STAT_WEIGHTS else "warrior"
        self.level = max(1, min(int(level), self.LEVEL_CAP))
        self.talent_points_total = self.level * self.TALENT_POINTS_PER_LEVEL
        self.learned_talents = {}
        self.glyph_slots = {
            kind: [None] * count for kind, count in self.GLYPH_SLOT_COUNTS.items()
        }
        self.skill_modifiers = {}
        self.gear = []
        self.base_attributes = {
            "strength": 100, "agility": 80, "intellect": 40, "stamina": 90,
        }
        self.attributes = dict(self.base_attributes)
        self.attribute_display = {}
        self.update_attributes()

    def _points_spent(self):
        return sum(self.learned_talents.values())

    def _points_available(self):
        return self.talent_points_total - self._points_spent()

    def _talent_blocker(self, talent_id):
        talent = self.TALENT_TREE[talent_id]
        for prereq in talent["prerequisites"]:
            if prereq not in self.learned_talents:
                return "missing_prerequisite"
        for conflict in talent["conflicts"]:
            if conflict in self.learned_talents:
                return "conflicting_talent"
        if self._points_available() <= 0:
            return "insufficient_talent_points"
        return None

    def learn_talent(self, talent_id=None, rank=1):
        """学习天赋：校验天赋树、天赋点，学习后应用属性加成。"""
        if talent_id is None:
            return self.calculate_talent_tree()
        talent = self.TALENT_TREE.get(talent_id)
        if talent is None:
            return {"success": False, "reason": "unknown_talent", "talent_id": talent_id}
        current_rank = self.learned_talents.get(talent_id, 0)
        rank = max(1, min(int(rank), talent["max_rank"] - current_rank))
        if current_rank >= talent["max_rank"]:
            return {"success": False, "reason": "max_rank_reached", "talent_id": talent_id}
        blocker = self._talent_blocker(talent_id)
        if blocker is not None:
            return {"success": False, "reason": blocker, "talent_id": talent_id}
        if self._points_available() < rank:
            return {"success": False, "reason": "insufficient_talent_points", "talent_id": talent_id}
        self.learned_talents[talent_id] = current_rank + rank
        display = self.update_attributes()
        return {
            "success": True,
            "talent_id": talent_id,
            "rank": self.learned_talents[talent_id],
            "points_available": self._points_available(),
            "attributes": display,
        }

    def calculate_talent_tree(self, reset=False):
        """天赋树：前置/互斥校验，支持洗点重置。"""
        if reset:
            self.learned_talents.clear()
            self.update_attributes()
        available = {}
        for talent_id, talent in self.TALENT_TREE.items():
            blocker = self._talent_blocker(talent_id)
            available[talent_id] = {
                "name": talent["name"],
                "tier": talent["tier"],
                "rank": self.learned_talents.get(talent_id, 0),
                "max_rank": talent["max_rank"],
                "prerequisites": list(talent["prerequisites"]),
                "conflicts": list(talent["conflicts"]),
                "can_learn": blocker is None,
                "reason": blocker,
            }
        return {
            "learned": dict(self.learned_talents),
            "points_total": self.talent_points_total,
            "points_spent": self._points_spent(),
            "points_available": self._points_available(),
            "available": available,
        }

    def apply_glyph(self, glyph_id=None, slot=None):
        """铭文：校验槽位类型与等级要求，插入后应用技能效果。"""
        if glyph_id is None:
            return {
                "slots": {kind: list(slots) for kind, slots in self.glyph_slots.items()},
                "skill_modifiers": dict(self.skill_modifiers),
            }
        glyph = self.GLYPHS.get(glyph_id)
        if glyph is None:
            return {"success": False, "reason": "unknown_glyph", "glyph_id": glyph_id}
        slot_type = glyph["slot"]
        if slot is not None and slot != slot_type:
            return {"success": False, "reason": "wrong_slot_type", "glyph_id": glyph_id}
        if self.level < glyph["required_level"]:
            return {"success": False, "reason": "level_too_low", "glyph_id": glyph_id}
        slots = self.glyph_slots[slot_type]
        if None not in slots:
            return {"success": False, "reason": "no_empty_slot", "glyph_id": glyph_id}
        index = slots.index(None)
        slots[index] = glyph_id
        effect = glyph["effect"]
        self.skill_modifiers[effect["skill"]] = dict(effect["bonus"])
        return {
            "success": True,
            "glyph_id": glyph_id,
            "slot": slot_type,
            "slot_index": index,
            "skill": effect["skill"],
            "effect": dict(effect["bonus"]),
        }

    def calculate_gear_stats(self, gear=None, hero_class=None):
        """配装：套装效果、职业属性权重、宝石插槽。"""
        gear = self.gear if gear is None else list(gear)
        weights = self.STAT_WEIGHTS.get(
            hero_class or self.hero_class, self.STAT_WEIGHTS["warrior"]
        )
        totals = {}
        gem_stats = {}
        set_counts = {}
        for item in gear:
            for stat, value in item.get("stats", {}).items():
                totals[stat] = totals.get(stat, 0) + value
            for gem in item.get("gems", []):
                for stat, value in gem.get("stats", {}).items():
                    gem_stats[stat] = gem_stats.get(stat, 0) + value
                    totals[stat] = totals.get(stat, 0) + value
            set_name = item.get("set")
            if set_name:
                set_counts[set_name] = set_counts.get(set_name, 0) + 1
        set_bonus_stats = {}
        for set_name, count in set_counts.items():
            for threshold, bonus in sorted(self.SET_BONUSES.get(set_name, {}).items()):
                if count >= threshold:
                    for stat, value in bonus.items():
                        set_bonus_stats[stat] = set_bonus_stats.get(stat, 0) + value
                        totals[stat] = totals.get(stat, 0) + value
        weighted_score = sum(
            totals.get(stat, 0) * weight for stat, weight in weights.items()
        )
        return {
            "stats": totals,
            "gem_stats": gem_stats,
            "set_bonuses": set_bonus_stats,
            "active_sets": dict(set_counts),
            "weights": dict(weights),
            "weighted_score": weighted_score,
        }

    def update_attributes(self, base=None):
        """属性：换算派生属性、加上限、生成玩家可见的属性面板。"""
        if base is not None:
            self.base_attributes.update(base)
        attributes = dict(self.base_attributes)
        for talent_id, rank in self.learned_talents.items():
            for stat, value in self.TALENT_TREE[talent_id]["bonus"].items():
                attributes[stat] = attributes.get(stat, 0) + value * rank
        derived = {}
        for stat, value in attributes.items():
            for target, ratio in self.ATTRIBUTE_CONVERSION.get(stat, {}).items():
                derived[target] = derived.get(target, 0.0) + value * ratio
        capped = {stat: min(value, self.ATTRIBUTE_CAP) for stat, value in attributes.items()}
        capped_derived = {
            stat: min(value, self.ATTRIBUTE_CAP) for stat, value in derived.items()
        }
        self.attributes = capped
        self.attribute_display = {**capped, **capped_derived}
        self.state["attributes"] = dict(self.attribute_display)
        return dict(self.attribute_display)
