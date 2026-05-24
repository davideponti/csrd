"""
CSRD Comply — Step 30: Unit tests for Carbon Calculator (Scope 1, 2, 3).

Tests the math and logic of emission calculations.
"""
import pytest
from ai_engine.carbon_calculator.scope1 import Scope1Calculator
from ai_engine.carbon_calculator.scope2 import Scope2Calculator
from ai_engine.carbon_calculator.scope3 import Scope3Calculator


class TestScope1Calculator:
    """Unit test per calcolatore Scope 1."""

    def test_stationary_combustion_natural_gas(self):
        result = Scope1Calculator.calculate_stationary_combustion(
            natural_gas_kwh=10_000
        )
        # 10_000 * 0.184 = 1_840 kgCO2e → 1.84 tCO2e
        assert result["total_tco2e"] == 1.84
        assert result["category"] == "stationary_combustion"
        assert "natural_gas" in result["breakdown"]

    def test_stationary_combustion_multiple_fuels(self):
        result = Scope1Calculator.calculate_stationary_combustion(
            natural_gas_kwh=5_000,
            diesel_heating_litres=2_000,
            biomass_kwh=1_000,
        )
        # 5_000*0.184 = 920 + 2_000*2.68 = 5_360 + 1_000*0.018 = 18
        # Total = 6_298 kgCO2e → 6.298 tCO2e
        assert result["total_tco2e"] == 6.298
        assert len(result["breakdown"]) == 3

    def test_stationary_combustion_no_input(self):
        result = Scope1Calculator.calculate_stationary_combustion()
        assert result["total_tco2e"] == 0.0
        assert result["breakdown"] == {}

    def test_mobile_combustion_mixed_fleet(self):
        result = Scope1Calculator.calculate_mobile_combustion(
            diesel_km=10_000,
            petrol_km=5_000,
            electric_km=8_000,
        )
        # 10_000*0.17 = 1_700 + 5_000*0.155 = 775 + 8_000*0.05 = 400
        # Total = 2_875 kgCO2e → 2.875 tCO2e
        assert result["total_tco2e"] == 2.875
        assert result["category"] == "mobile_combustion"

    def test_mobile_combustion_diesel_truck(self):
        result = Scope1Calculator.calculate_mobile_combustion(
            diesel_truck_km=50_000
        )
        # 50_000 * 0.87 = 43_500 kgCO2e → 43.5 tCO2e
        assert result["total_tco2e"] == 43.5
        assert "diesel_truck" in result["breakdown"]

    def test_fugitive_emissions_r410a(self):
        result = Scope1Calculator.calculate_fugitive_emissions(r410a_kg=100)
        # 100 * 2088 = 208_800 kgCO2e → 208.8 tCO2e
        assert result["total_tco2e"] == 208.8
        assert result["category"] == "fugitive_emissions"

    def test_fugitive_emissions_multiple_refrigerants(self):
        result = Scope1Calculator.calculate_fugitive_emissions(
            r410a_kg=50, r134a_kg=30
        )
        # 50*2088 = 104_400 + 30*1430 = 42_900 = 147_300 kg → 147.3 tCO2e
        assert result["total_tco2e"] == 147.3

    def test_process_emissions_cement(self):
        result = Scope1Calculator.calculate_process_emissions(cement_tonnes=1_000)
        # 1_000 * 0.54 = 540 tCO2e
        assert result["total_tco2e"] == 540.0
        assert result["category"] == "process_emissions"

    def test_process_emissions_steel_both_methods(self):
        result = Scope1Calculator.calculate_process_emissions(
            steel_tonnes_bf_bof=500,
            steel_tonnes_eaf=200,
        )
        # 500*1.85 = 925 + 200*0.40 = 80 = 1_005 tCO2e
        assert result["total_tco2e"] == 1005.0

    def test_process_emissions_refrigerant_leak(self):
        result = Scope1Calculator.calculate_process_emissions(
            refrigerant_leak_kg=50
        )
        # 50 * 0.15 = 7.5 kgCO2e → 0.0075 tCO2e
        assert result["total_tco2e"] == 0.0075

    def test_total_scope1(self):
        stationary = Scope1Calculator.calculate_stationary_combustion(natural_gas_kwh=10_000)
        mobile = Scope1Calculator.calculate_mobile_combustion(diesel_km=10_000)
        total = Scope1Calculator.calculate_total_scope1(
            stationary=stationary,
            mobile=mobile,
        )
        # 1.84 + 1.70 = 3.54 tCO2e
        assert total["total_tco2e"] == 3.54
        assert total["scope"] == "1"
        assert len(total["categories"]) == 2

    def test_get_emission_factors(self):
        factors = Scope1Calculator.get_emission_factors(country="IT")
        assert "stationary_combustion" in factors
        assert "mobile_combustion" in factors
        assert factors["grid_electricity_factor"]["country"] == "IT"


class TestScope2Calculator:
    """Unit test per calcolatore Scope 2."""

    def test_location_based_italy(self):
        result = Scope2Calculator.calculate_location_based(
            electricity_kwh=100_000, country="IT"
        )
        # 100_000 * 0.286 = 28_600 kgCO2e → 28.6 tCO2e
        assert result["total_tco2e"] == 28.6
        assert result["method"] == "location_based"

    def test_location_based_france(self):
        result = Scope2Calculator.calculate_location_based(
            electricity_kwh=100_000, country="FR"
        )
        # 100_000 * 0.055 = 5_500 kgCO2e → 5.5 tCO2e
        assert result["total_tco2e"] == 5.5

    def test_location_based_default(self):
        result = Scope2Calculator.calculate_location_based(
            electricity_kwh=100_000, country="XX"
        )
        # Falls back to EU_avg: 100_000 * 0.276 = 27_600 → 27.6 tCO2e
        assert result["total_tco2e"] == 27.6
        assert result["country"] == "XX"

    def test_market_based_with_green_tariff(self):
        result = Scope2Calculator.calculate_market_based(
            electricity_kwh=100_000, country="IT", has_green_tariff=True
        )
        # Green tariff → 0 emissioni
        assert result["total_tco2e"] == 0.0
        assert result["has_green_tariff"] is True

    def test_market_based_no_green_tariff(self):
        result = Scope2Calculator.calculate_market_based(
            electricity_kwh=100_000, country="DE"
        )
        # 100_000 * 0.341 = 34_100 → 34.1 tCO2e
        assert result["total_tco2e"] == 34.1
        assert result["has_green_tariff"] is False

    def test_dual_reporting(self):
        result = Scope2Calculator.calculate_both_methods(
            electricity_kwh=100_000, country="IT"
        )
        assert result["scope"] == "2"
        assert "location_based" in result
        assert "market_based" in result
        assert result["location_based"]["total_tco2e"] == 28.6
        assert result["market_based"]["total_tco2e"] == 34.2
        # Difference should be 5.6 tCO2e
        assert result["difference_tco2e"] == 5.6

    def test_steam_heating_cooling(self):
        result = Scope2Calculator.calculate_steam_heating_cooling(
            energy_kwh=50_000
        )
        # 50_000 * 0.12 = 6_000 → 6.0 tCO2e
        assert result["total_tco2e"] == 6.0


class TestScope3Calculator:
    """Unit test per calcolatore Scope 3."""

    def test_get_factor_known_nace(self):
        factor = Scope3Calculator.get_factor("C10")
        assert factor == 0.45

    def test_get_factor_unknown_nace(self):
        factor = Scope3Calculator.get_factor("Z99")
        assert factor == 0.25  # Default

    def test_category_1_purchased_goods(self):
        result = Scope3Calculator.category_1_purchased_goods_spend_based(
            spend_eur=100_000, supplier_nace="C20"
        )
        # 100_000 * 0.89 = 89_000 kg → 89.0 tCO2e
        assert result["total_tco2e"] == 89.0
        assert result["category"] == 1
        assert result["name"] == "Purchased goods and services"

    def test_category_2_capital_goods(self):
        result = Scope3Calculator.category_2_capital_goods(
            spend_eur=200_000, nace_code="C28"
        )
        # 200_000 * 0.38 = 76_000 → 76.0 tCO2e
        assert result["total_tco2e"] == 76.0
        assert result["category"] == 2

    def test_category_3_fuel_energy(self):
        result = Scope3Calculator.category_3_fuel_and_energy_related(
            electricity_kwh=100_000,
            natural_gas_kwh=50_000,
            diesel_litres=10_000,
        )
        # 100_000*0.032 = 3_200 + 50_000*0.031 = 1_550 + 10_000*0.54 = 5_400
        # Total = 10_150 kg → 10.15 tCO2e
        assert result["total_tco2e"] == 10.15
        assert result["category"] == 3

    def test_category_4_upstream_transport(self):
        result = Scope3Calculator.category_4_upstream_transportation(
            tkm=500_000, transport_mode="truck"
        )
        # 500_000 * 0.062 = 31_000 kg → 31.0 tCO2e
        assert result["total_tco2e"] == 31.0

    def test_category_5_waste(self):
        result = Scope3Calculator.category_5_waste_generated(
            waste_kg=10_000, waste_type="plastic"
        )
        # 10_000 * 0.65 = 6_500 kg → 6.5 tCO2e
        assert result["total_tco2e"] == 6.5
        assert result["category"] == 5

    def test_category_6_business_travel(self):
        result = Scope3Calculator.category_6_business_travel(
            km=50_000, travel_mode="flight_short_haul"
        )
        # 50_000 * 0.156 = 7_800 kg → 7.8 tCO2e
        assert result["total_tco2e"] == 7.8

    def test_category_7_employee_commuting(self):
        result = Scope3Calculator.category_7_employee_commuting(
            employees=100, avg_commute_km=25, commuting_mode="car_alone",
            working_days=220,
        )
        # 100 * 25 * 220 = 550_000 km * 0.17 = 93_500 kg → 93.5 tCO2e
        assert result["total_tco2e"] == 93.5

    def test_category_8_upstream_leased(self):
        result = Scope3Calculator.category_8_upstream_leased_assets(
            leased_area_m2=500, energy_kwh=30_000
        )
        # 500*25 = 12_500 + 30_000*0.276 = 8_280 = 20_780 kg → 20.78 tCO2e
        assert result["total_tco2e"] == 20.78

    def test_category_9_downstream_transport(self):
        result = Scope3Calculator.category_9_downstream_transportation(
            tkm=300_000, transport_mode="ship"
        )
        # 300_000 * 0.015 = 4_500 kg → 4.5 tCO2e
        assert result["total_tco2e"] == 4.5

    def test_category_10_processing(self):
        result = Scope3Calculator.category_10_processing_of_sold_products(
            product_value_eur=500_000, processing_type="chemicals"
        )
        # 500_000 * 0.12 = 60_000 kg → 60.0 tCO2e
        assert result["total_tco2e"] == 60.0

    def test_category_11_use_of_sold_products(self):
        result = Scope3Calculator.category_11_use_of_sold_products(
            products_sold=10_000, avg_energy_kwh_per_unit=200
        )
        # 10_000 * 200 = 2_000_000 kWh * 0.276 = 552_000 kg → 552.0 tCO2e
        assert result["total_tco2e"] == 552.0

    def test_category_12_end_of_life(self):
        result = Scope3Calculator.category_12_end_of_life_sold_products(
            product_weight_kg=5, products_sold=10_000, disposal_method="landfill"
        )
        # 50_000 * 0.58 = 29_000 kg → 29.0 tCO2e
        assert result["total_tco2e"] == 29.0

    def test_category_13_downstream_leased(self):
        result = Scope3Calculator.category_13_downstream_leased_assets(
            leased_area_m2=1_000
        )
        # 1_000 * 30 = 30_000 kg → 30.0 tCO2e
        assert result["total_tco2e"] == 30.0

    def test_category_14_franchises(self):
        result = Scope3Calculator.category_14_franchises(
            num_franchises=10, avg_energy_kwh_per_franchise=50_000
        )
        # 10*50_000 = 500_000 * 0.276 = 138_000 kg → 138.0 tCO2e
        assert result["total_tco2e"] == 138.0

    def test_category_15_investments(self):
        result = Scope3Calculator.category_15_investments(
            investment_eur=1_000_000
        )
        # 1_000_000 * 0.10 = 100_000 kg → 100.0 tCO2e
        assert result["total_tco2e"] == 100.0

    def test_calculate_upstream_total(self):
        result = Scope3Calculator.calculate_upstream_total(
            company_nace="C10",
            total_spend_eur=1_000_000,
        )
        # 1_000_000 * 0.45 = 450_000 → 450.0 tCO2e simplified
        assert result["total_tco2e"] == 450.0
        assert result["scope"] == "3"
        assert result["scope3_type"] == "upstream"

    def test_calculate_upstream_total_with_categories(self):
        cat1 = Scope3Calculator.category_1_purchased_goods_spend_based(
            spend_eur=100_000, supplier_nace="C20"
        )
        cat4 = Scope3Calculator.category_4_upstream_transportation(
            tkm=50_000, transport_mode="truck"
        )
        result = Scope3Calculator.calculate_upstream_total(
            company_nace="C10",
            category_results=[cat1, cat4],
        )
        # 89.0 + 3.1 = 92.1 tCO2e
        assert result["total_tco2e"] == 92.1

    def test_calculate_total_scope3(self):
        upstream = Scope3Calculator.calculate_upstream_total(
            company_nace="C10",
            total_spend_eur=1_000_000,
        )
        cat9 = Scope3Calculator.category_9_downstream_transportation(
            tkm=100_000, transport_mode="truck"
        )
        downstream = Scope3Calculator.calculate_downstream_total(
            categories=[cat9]
        )
        result = Scope3Calculator.calculate_total_scope3(
            upstream=upstream, downstream=downstream
        )
        # 450.0 + 6.2 = 456.2 tCO2e
        assert result["total_tco2e"] == 456.2
        assert result["scope"] == "3"
