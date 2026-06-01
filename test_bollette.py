#!/usr/bin/env python3
"""
Test estrazione dati da bollette energetiche europee (gas ed elettricità)
per il calcolo della carbon footprint secondo il GHG Protocol.

Supporto multi-paese: IT, ES, DE, NL, UK, SE, PL.

Esegui: python3 test_bollette.py
"""
import sys
sys.path.insert(0, './CSRD-Comply/ai_engine')

from carbon_calculator.data_collector import DataCollectorService
import json


def test_ocr_sporco_enel():
    """Test 1: OCR sporco - bolletta ENEL elettricità (l→1, O→0)"""
    testo = """ENEl Energla S.p.A.
Codice Fattura: FPO2025-0001
Fornitore: Enel Energla
Periodo dal 01/03/2025 al 3l/03/2025
Energia consumata: 2.525,40 kWh
POD: IT00lE12345678
TOTALE DA PAGARE: € 520,30"""
    
    risultato = DataCollectorService.parse_utility_bill_pdf_text(testo)
    print("=== TEST 1: OCR sporco (ENEL elettricità) ===")
    print(json.dumps(risultato, indent=2, ensure_ascii=False))
    print()
    
    # Verifiche
    assert risultato["paese"] == "IT", f"Paese non corretto: {risultato['paese']}"
    assert risultato["fornitore"] is not None, "Fornitore non trovato!"
    assert risultato["tipo"] == "electricity", "Tipo non corretto!"
    assert risultato["consumo_kwh"] is not None, "Consumo non trovato!"
    assert risultato["costo"] is not None, "Costo non trovato!"
    assert risultato["periodo_inizio"] is not None, "Periodo inizio non trovato!"
    assert risultato["periodo_fine"] is not None, "Periodo fine non trovato!"
    assert risultato["codice_utenza"] is not None, "POD non trovato!"
    assert risultato["valuta"] == "EUR", f"Valuta non corretta: {risultato['valuta']}"
    assert risultato["confidenza"] >= 50, f"Confidenza troppo bassa: {risultato['confidenza']}"
    print("✓ TEST 1 PASSATO")
    print()


def test_gas_ocr_sporco():
    """Test 2: Bolletta gas con OCR sporco"""
    testo = """ll servizio gas S.p.A.
Fornitore: Estra Energie
PDR: IT002G98765432
Periodo dal Ol/O4/2025 al 30/04/2025
Consumo totale: 1.200,50 Smc
Energia termica: 12.850,OO kWh
TOTALE FATTURA: € 890,75"""
    
    risultato = DataCollectorService.parse_utility_bill_pdf_text(testo)
    print("=== TEST 2: Bolletta gas con OCR ===")
    print(json.dumps(risultato, indent=2, ensure_ascii=False))
    print()
    
    assert risultato["paese"] == "IT", f"Paese non corretto: {risultato['paese']}"
    assert risultato["tipo"] == "gas", f"Tipo non corretto: {risultato['tipo']}"
    assert risultato["fornitore"] is not None, "Fornitore non trovato!"
    assert risultato["consumo_kwh"] is not None, "Consumo kWh non trovato!"
    assert risultato["costo"] is not None, "Costo non trovato!"
    assert risultato["codice_utenza"] is not None, "PDR non trovato!"
    assert risultato["valuta"] == "EUR", f"Valuta non corretta: {risultato['valuta']}"
    assert risultato["consumo_originale"] is not None, "Consumo originale non trovato!"
    assert risultato["unita_originale"] in ("Smc", "mc", "m³"), f"Unità non corretta: {risultato['unita_originale']}"
    print("✓ TEST 2 PASSATO")
    print()


def test_bolletta_spagnola():
    """Test 3: Bolletta spagnola (Iberdrola - CUPS)"""
    testo = """Iberdrola Clientes S.A.U.
Factura de electricidad
Nº factura: F2025-12345
Periodo de facturación: del 01/03/2025 al 31/03/2025
CUPS: ES002211223344556677AABB
Consumo total: 1.850 kWh
Importe total: 210,50 €
Total a pagar: 210,50 €"""
    
    risultato = DataCollectorService.parse_utility_bill_pdf_text(testo)
    print("=== TEST 3: Bolletta Spagna (Iberdrola) ===")
    print(json.dumps(risultato, indent=2, ensure_ascii=False))
    print()
    
    assert risultato["paese"] == "ES", f"Paese non corretto: {risultato['paese']}"
    assert risultato["tipo"] == "electricity", f"Tipo non corretto: {risultato['tipo']}"
    assert risultato["codice_utenza"] is not None, "CUPS non trovato!"
    assert risultato["fornitore"] is not None, "Fornitore non trovato!"
    print("✓ TEST 3 PASSATO")
    print()


def test_bolletta_tedesca():
    """Test 4: Bolletta tedesca (E.ON - MaLo-ID)"""
    testo = """E.ON Energie Deutschland GmbH
Rechnungsnummer: R2025-67890
Kunde: 1234567890
MaLo-ID: 12345678901
Zeitraum: 01.03.2025 - 31.03.2025
Verbrauch: 1.950 kWh
Gesamtbetrag: 345,90 €
Zählernummer: 98765432101"""
    
    risultato = DataCollectorService.parse_utility_bill_pdf_text(testo)
    print("=== TEST 4: Bolletta Germania (E.ON) ===")
    print(json.dumps(risultato, indent=2, ensure_ascii=False))
    print()
    
    assert risultato["paese"] == "DE", f"Paese non corretto: {risultato['paese']}"
    assert risultato["tipo"] == "electricity", f"Tipo non corretto: {risultato['tipo']}"
    assert risultato["codice_utenza"] is not None, "MaLo-ID non trovato!"
    assert risultato["fornitore"] is not None, "Fornitore non trovato!"
    assert risultato["valuta"] == "EUR", f"Valuta non corretta: {risultato['valuta']}"
    print("✓ TEST 4 PASSATO")
    print()


def test_bolletta_olandese():
    """Test 5: Bolletta olandese (Essent - EAN)"""
    testo = """Essent N.V.
Factuur: F2025-11111
Klantnummer: NL123456789
EAN code: 871234567890123456
Periode: 01-03-2025 tot 31-03-2025
Energieverbruik: 2.100 kWh
Totaal te betalen: € 298,75"""
    
    risultato = DataCollectorService.parse_utility_bill_pdf_text(testo)
    print("=== TEST 5: Bolletta Olanda (Essent) ===")
    print(json.dumps(risultato, indent=2, ensure_ascii=False))
    print()
    
    assert risultato["paese"] == "NL", f"Paese non corretto: {risultato['paese']}"
    assert risultato["tipo"] == "electricity", f"Tipo non corretto: {risultato['tipo']}"
    assert risultato["codice_utenza"] is not None, "EAN non trovato!"
    assert risultato["fornitore"] is not None, "Fornitore non trovato!"
    assert risultato["valuta"] == "EUR", f"Valuta non corretta: {risultato['valuta']}"
    print("✓ TEST 5 PASSATO")
    print()


def test_bolletta_uk():
    """Test 6: Bolletta UK (British Gas - MPAN/MPRN)"""
    testo = """British Gas Trading Limited
Invoice number: INV-2025-22222
Electricity Supply Number: 1234567890123
MPAN: 1234567890123
Period: from 01/03/2025 to 31/03/2025
Energy used: 1.250 kWh
Total amount due: £ 185,60"""
    
    risultato = DataCollectorService.parse_utility_bill_pdf_text(testo)
    print("=== TEST 6: Bolletta UK (British Gas) ===")
    print(json.dumps(risultato, indent=2, ensure_ascii=False))
    print()
    
    assert risultato["paese"] == "UK", f"Paese non corretto: {risultato['paese']}"
    assert risultato["tipo"] == "electricity", f"Tipo non corretto: {risultato['tipo']}"
    assert risultato["codice_utenza"] is not None, "MPAN non trovato!"
    assert risultato["fornitore"] is not None, "Fornitore non trovato!"
    assert risultato["valuta"] == "GBP", f"Valuta non corretta: {risultato['valuta']}"
    print("✓ TEST 6 PASSATO")
    print()


def test_bolletta_svedese():
    """Test 7: Bolletta svedese (Vattenfall - MELO)"""
    testo = """Vattenfall AB
Faktura: F2025-33333
MELO: SE123456789
Period: 2025-03-01 - 2025-03-31
Energiförbrukning: 2.500 kWh
Totalt att betala: 3.450,50 kr"""
    
    risultato = DataCollectorService.parse_utility_bill_pdf_text(testo)
    print("=== TEST 7: Bolletta Svezia (Vattenfall) ===")
    print(json.dumps(risultato, indent=2, ensure_ascii=False))
    print()
    
    assert risultato["paese"] == "SE", f"Paese non corretto: {risultato['paese']}"
    assert risultato["tipo"] == "electricity", f"Tipo non corretto: {risultato['tipo']}"
    assert risultato["codice_utenza"] is not None, "MELO non trovato!"
    assert risultato["fornitore"] is not None, "Fornitore non trovato!"
    assert risultato["valuta"] == "SEK", f"Valuta non corretta: {risultato['valuta']}"
    print("✓ TEST 7 PASSATO")
    print()


def test_bolletta_polacca():
    """Test 8: Bolletta polacca (PGE - PPE)"""
    testo = """PGE Polska Grupa Energetyczna
Faktura: F2025-44444
PPE: 12345678901
Okres: od 01.03.2025 do 31.03.2025
Zużycie energii: 1.800 kWh
Łączna kwota: 720,50 zł"""
    
    risultato = DataCollectorService.parse_utility_bill_pdf_text(testo)
    print("=== TEST 8: Bolletta Polonia (PGE) ===")
    print(json.dumps(risultato, indent=2, ensure_ascii=False))
    print()
    
    assert risultato["paese"] == "PL", f"Paese non corretto: {risultato['paese']}"
    assert risultato["tipo"] == "electricity", f"Tipo non corretto: {risultato['tipo']}"
    assert risultato["codice_utenza"] is not None, "PPE non trovato!"
    assert risultato["fornitore"] is not None, "Fornitore non trovato!"
    assert risultato["valuta"] == "PLN", f"Valuta non corretta: {risultato['valuta']}"
    print("✓ TEST 8 PASSATO")
    print()


def test_lettura_stimata():
    """Test 9: Rilevamento lettura stimata"""
    testo = """Enel Energia S.p.A.
Periodo dal 01/04/2025 al 30/04/2025
Consumo: 1.200 kWh (lettura stimata)
POD: IT001E12345678
Totale da pagare: € 280,00"""
    
    risultato = DataCollectorService.parse_utility_bill_pdf_text(testo)
    print("=== TEST 9: Lettura stimata ===")
    print(json.dumps(risultato, indent=2, ensure_ascii=False))
    print()
    
    assert risultato["lettura_stimata"] == True, "Dovrebbe rilevare lettura stimata!"
    assert risultato["confidenza"] <= 95, f"Confidenza dovrebbe essere ridotta: {risultato['confidenza']}"
    print("✓ TEST 9 PASSATO")
    print()


def test_testo_minimo():
    """Test 10: Testo minimo (pochi dati) -> bassa confidenza"""
    risultato = DataCollectorService.parse_utility_bill_pdf_text("Bolletta Enel")
    print("=== TEST 10: Testo minimo ===")
    print(json.dumps(risultato, indent=2, ensure_ascii=False))
    print()
    
    assert risultato["confidenza"] < 50, f"Confidenza dovrebbe essere bassa: {risultato['confidenza']}"
    print("✓ TEST 10 PASSATO")
    print()


def test_bolletta_gas_tedesca():
    """Test 11: Bolletta gas tedesca con consumo in Nm³"""
    testo = """Stadtwerke München GmbH
Gasrechnung: R2025-55555
MaLo-ID: 98765432109
Zeitraum: 01.02.2025 - 28.02.2025
Verbrauch: 850 kWh
Gasverbrauch: 85 Nm³
Gesamtbetrag: 125,40 €"""
    
    risultato = DataCollectorService.parse_utility_bill_pdf_text(testo)
    print("=== TEST 11: Bolletta Gas Germania (Stadtwerke) ===")
    print(json.dumps(risultato, indent=2, ensure_ascii=False))
    print()
    
    assert risultato["paese"] == "DE", f"Paese non corretto: {risultato['paese']}"
    assert risultato["tipo"] == "gas", f"Tipo non corretto: {risultato['tipo']}"
    assert risultato["consumo_kwh"] is not None, "Consumo kWh non trovato!"
    assert risultato["codice_utenza"] is not None, "MaLo-ID non trovato!"
    print("✓ TEST 11 PASSATO")
    print()


def test_preprocessing():
    """Test 12: Verifica pre-processing OCR isolato"""
    print("=== TEST 12: Pre-processing OCR ===")
    
    # l→1 in contesto numerico
    assert DataCollectorService._preprocess_ocr_text("3l/03/2025") == "31/03/2025"
    # O→0 in contesto numerico
    assert DataCollectorService._preprocess_ocr_text("12.850,OO") == "12.850.00"
    # Virgola decimale → punto
    assert DataCollectorService._preprocess_ocr_text("2.525,40") == "2.525.40"
    # Spazi doppi
    assert DataCollectorService._preprocess_ocr_text("Enel   Energia") == "Enel Energia"
    
    print("✓ TEST 12 PASSATO")
    print()


def test_confidenza_ocr_noise():
    """Test 13: Confidenza si riduce con OCR noise"""
    testo_pulito = """Enel Energia S.p.A.
Periodo dal 01/03/2025 al 31/03/2025
Consumo: 1.850 kWh
POD: IT001E12345678
Totale da pagare: € 450,80"""

    testo_sporco = """ENEl Energla S.p.A.
Periodo dal 01/03/2025 al 3l/03/2025
Energia consumata: 2.525,40 kWh
POD: IT00lE12345678
TOTALE DA PAGARE: € 520,30"""
    
    pulito = DataCollectorService.parse_utility_bill_pdf_text(testo_pulito)
    sporco = DataCollectorService.parse_utility_bill_pdf_text(testo_sporco)
    
    print("=== TEST 13: Confidenza OCR noise ===")
    print(f"Confidenza testo pulito: {pulito['confidenza']}")
    print(f"Confidenza testo sporco: {sporco['confidenza']}")
    print()
    
    assert pulito["confidenza"] >= sporco["confidenza"], "OCR noise dovrebbe ridurre confidenza!"
    print("✓ TEST 13 PASSATO")
    print()


if __name__ == "__main__":
    test_preprocessing()
    test_ocr_sporco_enel()
    test_gas_ocr_sporco()
    test_bolletta_spagnola()
    test_bolletta_tedesca()
    test_bolletta_olandese()
    test_bolletta_uk()
    test_bolletta_svedese()
    test_bolletta_polacca()
    test_lettura_stimata()
    test_bolletta_gas_tedesca()
    test_testo_minimo()
    test_confidenza_ocr_noise()
    
    print("=" * 40)
    print("TUTTI I TEST SUPERATI! 🎉")
    print("=" * 40)
