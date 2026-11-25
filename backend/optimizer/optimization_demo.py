from backend.calculator.carbon_calculator import calculate_event_footprint
from backend.optimizer.event_optimizer import optimize_event


# ==================================================
# EVENT INPUT
# ==================================================

attendees = 100
distance_km = 10
meals = 100
energy_kwh = 500
waste_kg = 50
materials_kg = 20


# ==================================================
# BASELINE
# ==================================================

baseline = calculate_event_footprint(
    attendees=attendees,
    distance_km=distance_km,
    meals=meals,
    energy_kwh=energy_kwh,
    waste_kg=waste_kg,
    materials_kg=materials_kg
)


# ==================================================
# OPTIMIZATION
# ==================================================

optimized = optimize_event(
    attendees=attendees,
    budget=15000,
    max_car_percent=30
)


# ==================================================
# TRANSPORT EMISSIONS
# ==================================================

# Baseline transport:
# 0.067 kg CO2e per passenger-km

baseline_transport = (
    attendees
    * distance_km
    * 0.067
)


# Optimizer uses its own relative transport
# emission scores:
#
# Car   = 10
# Bus   = 4
# Metro = 2
#
# We convert the optimized score into
# the same baseline transport scale.

optimized_transport_score = optimized["estimated_co2"]

baseline_transport_score = (
    attendees * 10
)

optimized_transport = (
    baseline_transport
    * optimized_transport_score
    / baseline_transport_score
)


# ==================================================
# OPTIMIZED TOTAL
# ==================================================

optimized_total = (
    baseline["total_co2e"]
    - baseline_transport
    + optimized_transport
)


# ==================================================
# REDUCTION
# ==================================================

reduction = (
    baseline["total_co2e"]
    - optimized_total
)

reduction_percent = (
    reduction
    / baseline["total_co2e"]
    * 100
)


# ==================================================
# OUTPUT
# ==================================================

print("\nSUSTAINABLE EVENT OPTIMIZATION")
print("=" * 60)

print(
    f"Baseline CO2:      "
    f"{baseline['total_co2e']:.2f} kg CO2e"
)

print(
    f"Baseline Transport:"
    f" {baseline_transport:.2f} kg CO2e"
)

print(
    f"Optimized Transport:"
    f" {optimized_transport:.2f} kg CO2e"
)

print(
    f"Optimized CO2:     "
    f"{optimized_total:.2f} kg CO2e"
)

print(
    f"CO2 Reduction:     "
    f"{reduction:.2f} kg CO2e"
)

print(
    f"Reduction Percent: "
    f"{reduction_percent:.2f}%"
)

print("\nOPTIMIZED TRANSPORT PLAN")
print("=" * 60)

print(
    f"Car:   {optimized['car_attendees']}"
)

print(
    f"Bus:   {optimized['bus_attendees']}"
)

print(
    f"Metro: {optimized['metro_attendees']}"
)

print(
    f"Cost:  ₹{optimized['estimated_cost']}"
)