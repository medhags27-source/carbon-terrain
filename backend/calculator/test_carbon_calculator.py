from carbon_calculator import calculate_event_footprint


result = calculate_event_footprint(
    attendees=100,
    distance_km=10,
    meals=100,
    energy_kwh=500,
    waste_kg=50,
    materials_kg=20
)


print("\n--- EVENT CARBON FOOTPRINT ---")

print(f"Transport: {result['transport']:.2f} kg CO2e")
print(f"Food:      {result['food']:.2f} kg CO2e")
print(f"Energy:    {result['energy']:.2f} kg CO2e")
print(f"Waste:     {result['waste']:.2f} kg CO2e")
print(f"Materials: {result['materials']:.2f} kg CO2e")

print("-------------------------------")

print(f"TOTAL:     {result['total_co2e']:.2f} kg CO2e")