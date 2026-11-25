import re

from backend.agent.planning_engine import EventPlanningEngine


class EventAssistant:

    def __init__(self, initial_state):
        self.engine = EventPlanningEngine(initial_state)

        # Create the initial baseline plan.
        self.engine.optimize()

        # Create the initial baseline plan.
        self.engine.optimize()

    def _build_change_summary(self, result):
        previous = result.get("previous_plan")
        current = result.get("current_plan")

        if not previous or not current:
            return None

        previous_plan = previous.get("optimized_plan", {})
        current_plan = current.get("optimized_plan", {})

        previous_co2 = previous_plan.get("estimated_co2_kg", 0)
        current_co2 = current_plan.get("estimated_co2_kg", 0)

        previous_cost = previous_plan.get("estimated_cost", 0)
        current_cost = current_plan.get("estimated_cost", 0)

        return {
            "before": {
                "attendees": previous.get("inputs", {}).get("attendees"),
                "budget": previous.get("inputs", {}).get("budget"),
                "car_attendees": previous_plan.get("car_attendees"),
                "bus_attendees": previous_plan.get("bus_attendees"),
                "co2_kg": previous_co2,
                "cost": previous_cost
            },
            "after": {
                "attendees": current.get("inputs", {}).get("attendees"),
                "budget": current.get("inputs", {}).get("budget"),
                "car_attendees": current_plan.get("car_attendees"),
                "bus_attendees": current_plan.get("bus_attendees"),
                "co2_kg": current_co2,
                "cost": current_cost
            },
            "change": {
                "co2_kg": round(current_co2 - previous_co2, 2),
                "cost": round(current_cost - previous_cost, 2),
                "car_attendees": (
                    current_plan.get("car_attendees", 0)
                    - previous_plan.get("car_attendees", 0)
                ),
                "bus_attendees": (
                    current_plan.get("bus_attendees", 0)
                    - previous_plan.get("bus_attendees", 0)
                )
            },
            "explanation": current.get("explanation")
        }

    def process(self, message):
        text = message.lower().strip()
        current_state = self.engine.get_state()
        current = current_state.get("budget", 0)

        # -----------------------------
        # BUDGET
        # -----------------------------
        if "budget" in text:

            match = re.search(
                r"(?:increase|raise|add|set|make|keep)\s+"
                r"(?:my\s+)?budget\s+(?:to\s+)?([0-9][0-9,]*)",
                text
            )

            if match:
                new_budget = float(match.group(1).replace(",", ""))

                result = self.engine.update_event({
                    "budget": new_budget
                })

                comparison = self._build_change_summary(result)

                return {
                    "success": True,
                    "action": "budget_updated",
                    "message": (
                        f"Budget changed from {current:,.0f} "
                        f"to {new_budget:,.0f}. "
                        "The event plan has been re-optimized."
                    ),
                    "result": result,
                    "comparison": comparison,
                    "state": self.engine.get_state()
                }

            match = re.search(
                r"(?:decrease|reduce|lower)\s+"
                r"(?:my\s+)?budget\s+(?:to\s+)?([0-9][0-9,]*)",
                text
            )

            if match:
                new_budget = float(match.group(1).replace(",", ""))

                result = self.engine.update_event({
                    "budget": new_budget
                })

                comparison = self._build_change_summary(result)

                return {
                    "success": True,
                    "action": "budget_updated",
                    "message": (
                        f"Budget reduced from {current:,.0f} "
                        f"to {new_budget:,.0f}. "
                        "The event plan has been re-optimized."
                    ),
                    "result": result,
                    "comparison": comparison,
                    "state": self.engine.get_state()
                }

        # -----------------------------
        # ATTENDANCE
        # -----------------------------

        # Standard attendance update:
        # "increase attendance to 1500"
        # "set attendees to 1500"
        match = re.search(
            r"(?:increase|raise|set|make)\s+"
            r"(?:attendance|attendees|students)\s+"
            r"(?:to\s+)?([0-9][0-9,]*)",
            text
        )

        # Natural-language scenario/update:
        # "what if 1500 students attend?"
        # "what if attendance is 1500?"
        # "what if we have 1500 attendees?"
        if not match:
            match = re.search(
                r"what\s+if\s+"
                r"(?:we\s+have\s+)?"
                r"([0-9][0-9,]*)\s+"
                r"(?:students|attendees)\s+attend",
                text
            )

        if not match:
            match = re.search(
                r"what\s+if\s+"
                r"(?:attendance|attendees)\s+"
                r"(?:is|are|becomes?)\s+"
                r"([0-9][0-9,]*)",
                text
            )

        if match:
            new_attendees = int(match.group(1).replace(",", ""))

            result = self.engine.update_event({
                "attendees": new_attendees
            })

            comparison = self._build_change_summary(result)

            return {
                "success": True,
                "action": "attendance_updated",
                "message": (
                    f"Attendance updated to {new_attendees}. "
                    "The event plan has been re-optimized."
                ),
                "result": result,
                "comparison": comparison,
                "state": self.engine.get_state()
            }

        # -----------------------------
        # OPTIMIZE
        # -----------------------------
        if (
            text.strip() in {
                "optimize",
                "optimise",
                "optimize event",
                "optimise event",
                "re-optimize",
                "reoptimise",
                "run optimization",
                "run optimisation",
            }
            or text.strip().startswith((
                "optimize event ",
                "optimise event ",
                "run optimization ",
                "run optimisation ",
            ))
        ):
            result = self.engine.optimize()

            return {
                "success": True,
                "action": "optimization",
                "message": (
                    "The event plan has been optimized "
                    "under the current constraints."
                ),
                "result": result,
                "state": self.engine.get_state()
            }

        # -----------------------------
        # COMPARE
        # -----------------------------
        if "compare" in text:
            comparison = self.engine.get_comparison()

            return {
                "success": True,
                "action": "comparison",
                "message": (
                    "Here is the comparison between the "
                    "previous and current event plan."
                ),
                "result": comparison,
                "comparison": self._build_change_summary(comparison),
                "state": self.engine.get_state()
            }

        # -----------------------------
        # EVENT-AWARE FALLBACK
        # -----------------------------
        state = self.engine.get_state()

        attendees = int(state.get("attendees", 0) or 0)
        budget = float(state.get("budget", 0) or 0)
        distance = float(state.get("distance_km", 0) or 0)
        meals = float(state.get("meals", 0) or 0)

        message_text = (
            f"Your current event has {attendees:,} attendees, "
            f"a budget of ₹{budget:,.0f}, "
            f"an average travel distance of {distance:g} km, "
            f"and {meals:g} meals per person. "
            "To reduce emissions, review transport, lower-carbon "
            "food, energy use, waste reduction, and reusable materials. "
            "Use Optimize Event to obtain the available estimated "
            "carbon savings and costs for your current event. "
            "You can also ask me to compare attendance scenarios, "
            "test a budget, or set a carbon limit."
        )

        return {
            "success": True,
            "action": "event_aware_response",
            "message": message_text,
            "state": state
        }

