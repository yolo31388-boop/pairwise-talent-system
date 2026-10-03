"""MMO talent, glyph, gear, and attribute system."""


class TalentSystem:
    """Core MMO character system: talent tree, glyphs, gear, and attributes."""

    ATTRIBUTE_CAPS = {
        "strength": 100,
        "agility": 100,
        "intellect": 100,
        "stamina": 100,
    }

    DERIVED_CONVERSIONS = {
        "attack_power": ("strength", 2),
        "spell_power": ("intellect", 2),
        "crit_chance": ("agility", 0.1),
        "max_health": ("stamina", 10),
    }

    TALENT_TREE = {
        "improved_strike": {
            "tier": 1, "max_rank": 3, "cost": 1,
            "requires": {}, "conflicts_with": [],
            "effect": {"strength": 5},
        },
        "toughness": {
            "tier": 1, "max_rank": 3, "cost": 1,
            "requires": {}, "conflicts_with": [],
            "effect": {"stamina": 5},
        },
        "power_surge": {
            "tier": 2, "max_rank": 2, "cost": 1,
            "requires": {"improved_strike": 3}, "conflicts_with": ["arcane_focus"],
            "effect": {"strength": 15},
        },
        "arcane_focus": {
            "tier": 2, "max_rank": 2, "cost": 1,
            "requires": {"toughness": 2}, "conflicts_with": ["power_surge"],
            "effect": {"intellect": 10},
        },
        "ultimate_power": {
            "tier": 3, "max_rank": 1, "cost": 2,
            "requires": {"power_surge": 2}, "conflicts_with": [],
            "effect": {"strength": 50},
        },
    }

    GLYPHS = {
        "glyph_of_power": {
            "type": "major", "required_level": 20,
            "effect": {"skill": "strike", "bonus": {"damage": 20}},
        },
        "glyph_of_sweeping": {
            "type": "major", "required_level": 40,
            "effect": {"skill": "strike", "bonus": {"targets": 2}},
        },
        "glyph_of_recovery": {
            "type": "minor", "required_level": 10,
            "effect": {"skill": "heal", "bonus": {"healing": 15}},
        },
        "glyph_of_haste": {
            "type": "minor", "required_level": 50,
            "effect": {"skill": "heal", "bonus": {"cooldown": -2}},
        },
    }

    GLYPH_SLOTS = ("major_1", "major_2", "major_3", "minor_1", "minor_2", "minor_3")

    SET_BONUSES = {
        "warlord": {2: {"strength": 20}, 4: {"strength": 30}},
        "sage": {2: {"intellect": 20}, 4: {"intellect": 30}},
    }

    GEM_STATS = {
        "ruby": {"strength": 10},
        "sapphire": {"intellect": 10},
        "emerald": {"agility": 10},
        "topaz": {"stamina": 10},
    }

    DEFAULT_STAT_WEIGHTS = {
        "strength": 1.0,
        "agility": 1.2,
        "intellect": 0.8,
        "stamina": 0.5,
        "attack_power": 0.5,
        "spell_power": 0.5,
    }

    DEFAULT_SKILLS = {
        "strike": {"damage": 100, "cooldown": 6, "targets": 1},
        "heal": {"healing": 80, "cooldown": 8},
    }

    def __init__(self, level=60, talent_points=None, attributes=None, stat_weights=None):
        self.state = {}
        self.level = level
        self.total_talent_points = (
            talent_points if talent_points is not None else max(0, level - 9)
        )
        self.talent_points = self.total_talent_points
        self.learned_talents = {}
        self.talent_bonuses = {}
        self.glyphs = {}
        self.skills = {name: dict(stats) for name, stats in self.DEFAULT_SKILLS.items()}
        self.gear = []
        self.base_attributes = {
            "strength": 10, "agility": 10, "intellect": 10, "stamina": 10,
        }
        if attributes:
            self.base_attributes.update(attributes)
        self.stat_weights = dict(self.DEFAULT_STAT_WEIGHTS)
        if stat_weights:
            self.stat_weights.update(stat_weights)
        self.attributes = {}
        self.update_attributes()

    # ------------------------------------------------------------------
    # Talents
    # ------------------------------------------------------------------
    def learn_talent(self, talent=None, rank=None, **kwargs):
        """Learn a talent: respects the tree, prerequisites, conflicts,
        talent points, and applies the talent's stat bonus."""
        if talent is None:
            return self._talent_summary()
        node = self.TALENT_TREE.get(talent)
        if node is None:
            return False
        current = self.learned_talents.get(talent, 0)
        target = current + 1 if rank is None else rank
        if target <= current or target > node["max_rank"]:
            return False
        for req, req_rank in node["requires"].items():
            if self.learned_talents.get(req, 0) < req_rank:
                return False
        for conflict in node["conflicts_with"]:
            if self.learned_talents.get(conflict, 0) > 0:
                return False
        cost = node["cost"] * (target - current)
        if cost > self.talent_points:
            return False
        self.talent_points -= cost
        self.learned_talents[talent] = target
        for stat, value in node["effect"].items():
            self.talent_bonuses[stat] = (
                self.talent_bonuses.get(stat, 0) + value * (target - current)
            )
        self.update_attributes()
        return self._talent_summary()

    def calculate_talent_tree(self, build=None, reset=False, **kwargs):
        """Validate a talent build (prerequisites, mutual exclusion, point
        budget) or reset the tree and refund all points."""
        if reset:
            return self.reset_talents()
        if build is None:
            return self._talent_summary()
        errors = []
        total_cost = 0
        for name, rank in build.items():
            node = self.TALENT_TREE.get(name)
            if node is None:
                errors.append(f"unknown talent: {name}")
                continue
            if rank < 1 or rank > node["max_rank"]:
                errors.append(f"{name}: rank {rank} out of range")
            for req, req_rank in node["requires"].items():
                known = max(build.get(req, 0), self.learned_talents.get(req, 0))
                if known < req_rank:
                    errors.append(f"{name}: requires {req} rank {req_rank}")
            for conflict in node["conflicts_with"]:
                if build.get(conflict, 0) > 0 or self.learned_talents.get(conflict, 0) > 0:
                    errors.append(f"{name}: conflicts with {conflict}")
            total_cost += node["cost"] * rank
        if total_cost > self.total_talent_points:
            errors.append("not enough talent points")
        return {
            "valid": not errors,
            "errors": errors,
            "cost": total_cost,
            "talent_points": self.talent_points,
        }

    def reset_talents(self):
        """Unlearn every talent and refund all talent points."""
        self.learned_talents.clear()
        self.talent_bonuses.clear()
        self.talent_points = self.total_talent_points
        self.update_attributes()
        return self._talent_summary()

    def _talent_summary(self):
        return {
            "learned": dict(self.learned_talents),
            "talent_points": self.talent_points,
            "total_talent_points": self.total_talent_points,
            "bonuses": dict(self.talent_bonuses),
        }

    # ------------------------------------------------------------------
    # Glyphs
    # ------------------------------------------------------------------
    def apply_glyph(self, glyph=None, slot=None, **kwargs):
        """Socket a glyph: enforces slot type, level requirement, and
        applies the glyph's effect to its skill."""
        if glyph is None:
            return self._glyph_summary()
        spec = self.GLYPHS.get(glyph)
        if spec is None:
            return False
        if self.level < spec["required_level"]:
            return False
        if slot is None:
            slot = next(
                (
                    s for s in self.GLYPH_SLOTS
                    if s.startswith(spec["type"]) and s not in self.glyphs
                ),
                None,
            )
            if slot is None:
                return False
        if slot not in self.GLYPH_SLOTS:
            return False
        if not slot.startswith(spec["type"]):
            return False
        if slot in self.glyphs:
            self._remove_glyph_effect(self.GLYPHS[self.glyphs[slot]])
        self.glyphs[slot] = glyph
        self._apply_glyph_effect(spec)
        return self._glyph_summary()

    def remove_glyph(self, slot):
        if slot not in self.glyphs:
            return False
        self._remove_glyph_effect(self.GLYPHS[self.glyphs.pop(slot)])
        return self._glyph_summary()

    def _apply_glyph_effect(self, spec):
        effect = spec["effect"]
        skill = self.skills.setdefault(effect["skill"], {})
        for key, value in effect["bonus"].items():
            skill[key] = skill.get(key, 0) + value

    def _remove_glyph_effect(self, spec):
        effect = spec["effect"]
        skill = self.skills.get(effect["skill"], {})
        for key, value in effect["bonus"].items():
            if key in skill:
                skill[key] -= value

    def _glyph_summary(self):
        return {
            "slots": {slot: self.glyphs.get(slot) for slot in self.GLYPH_SLOTS},
            "skills": {name: dict(stats) for name, stats in self.skills.items()},
        }

    # ------------------------------------------------------------------
    # Gear
    # ------------------------------------------------------------------
    def calculate_gear_stats(self, gear=None, weights=None, **kwargs):
        """Total gear stats including set bonuses, socketed gems, and a
        stat-weighted score."""
        if gear is None:
            gear = self.gear
        else:
            self.gear = list(gear)
        weights = dict(self.stat_weights)
        if kwargs.get("stat_weights"):
            weights.update(kwargs["stat_weights"])
        stats = {}
        set_counts = {}
        gems_applied = []
        for item in gear:
            for stat, value in item.get("stats", {}).items():
                stats[stat] = stats.get(stat, 0) + value
            set_name = item.get("set")
            if set_name:
                set_counts[set_name] = set_counts.get(set_name, 0) + 1
            sockets = item.get("sockets", 0)
            socket_count = sockets if isinstance(sockets, int) else len(sockets)
            for gem in item.get("gems", [])[:socket_count]:
                for stat, value in self.GEM_STATS.get(gem, {}).items():
                    stats[stat] = stats.get(stat, 0) + value
                gems_applied.append(gem)
        set_bonuses = []
        for set_name, count in set_counts.items():
            for threshold in sorted(self.SET_BONUSES.get(set_name, {})):
                if count >= threshold:
                    for stat, value in self.SET_BONUSES[set_name][threshold].items():
                        stats[stat] = stats.get(stat, 0) + value
                    set_bonuses.append(f"{set_name} ({threshold})")
        weighted_score = sum(
            value * weights.get(stat, 1.0) for stat, value in stats.items()
        )
        return {
            "stats": stats,
            "sets": set_counts,
            "set_bonuses": set_bonuses,
            "gems": gems_applied,
            "weighted_score": weighted_score,
        }

    # ------------------------------------------------------------------
    # Attributes
    # ------------------------------------------------------------------
    def update_attributes(self, attributes=None, **kwargs):
        """Recompute attributes: merges base + talent bonuses, enforces
        caps, converts primary stats into derived stats, and returns the
        current attribute display."""
        updates = dict(attributes or {})
        updates.update(kwargs)
        for stat, value in updates.items():
            self.base_attributes[stat] = self.base_attributes.get(stat, 0) + value
        primary = {}
        for stat in set(self.base_attributes) | set(self.talent_bonuses):
            raw = self.base_attributes.get(stat, 0) + self.talent_bonuses.get(stat, 0)
            cap = self.ATTRIBUTE_CAPS.get(stat)
            primary[stat] = min(raw, cap) if cap is not None else raw
        derived = {}
        for derived_stat, (source, factor) in self.DERIVED_CONVERSIONS.items():
            derived[derived_stat] = primary.get(source, 0) * factor
        self.attributes = {**primary, **derived}
        self.state["attributes"] = self.attributes
        return dict(self.attributes)

    def display_attributes(self):
        """Human-readable display of the current attributes."""
        if not self.attributes:
            self.update_attributes()
        return "\n".join(
            f"{name}: {value}" for name, value in sorted(self.attributes.items())
        )
