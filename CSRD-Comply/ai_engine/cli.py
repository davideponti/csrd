#!/usr/bin/env python3
"""
CSRD Comply — CLI Runner for AI Engine modules.

Usage:
  python cli.py seed-sustainability    # Seed sustainability matters
  python cli.py ingest-taxonomy       # Ingest ESRS taxonomy from Excel
  python cli.py seed-all              # Do both
  python cli.py gap-analysis <company_id>  # Run gap analysis
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1]

    if command == "seed-all":
        _run_seed()
        _run_ingest()
    elif command == "seed-sustainability":
        _run_seed()
    elif command == "ingest-taxonomy":
        _run_ingest()
    elif command == "gap-analysis":
        if len(sys.argv) < 3:
            print("Usage: python cli.py gap-analysis <company_id>")
            sys.exit(1)
        _run_gap_analysis(sys.argv[2])
    elif command == "generate-iros":
        if len(sys.argv) < 3:
            print("Usage: python cli.py generate-iros <company_id> [--use-ai]")
            sys.exit(1)
        use_ai = "--use-ai" in sys.argv
        _run_generate_iros(sys.argv[2], use_ai)
    elif command == "questionnaire":
        if len(sys.argv) < 4:
            print("Usage: python cli.py questionnaire <company_id> <sector_code>")
            sys.exit(1)
        _run_questionnaire(sys.argv[2], sys.argv[3])
    else:
        print(f"Unknown command: {command}")
        print(__doc__)
        sys.exit(1)


def _get_session():
    """Create a database session for CLI usage."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session

    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/csrd_comply",
    )
    engine = create_engine(database_url)
    return Session(engine)


def _run_seed():
    """Seed the sustainability_matters table."""
    from esrs_parser.ingest_taxonomy import seed_sustainability_matters

    print("🌱 Seeding sustainability matters...")
    db = _get_session()
    try:
        seed_sustainability_matters(db)
        print("✅ Sustainability matters seeded.")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()


def _run_ingest():
    """Ingest ESRS taxonomy from Excel file into the database."""
    from esrs_parser.ingest_taxonomy import ingest_taxonomy, seed_sustainability_matters

    excel_path = os.getenv("EXCEL_PATH", "data/efrag_ig3_datapoints.xlsx")

    if not os.path.exists(excel_path):
        print(f"⚠️  Excel file not found at: {excel_path}")
        print("   Set EXCEL_PATH env var or place the file at that location.")
        print("   Generating synthetic data for testing...")
        _generate_synthetic_data()
        return

    print(f"📄 Ingesting taxonomy from: {excel_path}")
    db = _get_session()
    try:
        count = ingest_taxonomy(db)
        print(f"✅ Ingested {count} datapoints.")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()


def _generate_synthetic_data():
    """Generate synthetic ESRS datapoints for testing/demo purposes."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session
    from backend.app.models import EsrsDatapoint

    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/csrd_comply",
    )
    engine = create_engine(database_url)

    with Session(engine) as db:
        # First seed sustainability matters
        from esrs_parser.ingest_taxonomy import seed_sustainability_matters
        seed_sustainability_matters(db)

        # Generate ~100 synthetic datapoints for demo
        synthetic_data = [
            # Environmental - E1 Climate
            ("ESRS E1-1", "1", "Transition plan for climate change mitigation", "narrative", True),
            ("ESRS E1-1", "2", "Description of climate resilience", "narrative", True),
            ("ESRS E1-2", "3", "Energy consumption mix (total MWh)", "numerical", True),
            ("ESRS E1-2", "4", "Share of renewable energy (%)", "numerical", True),
            ("ESRS E1-3", "5", "Energy intensity per net revenue (MWh/EUR)", "numerical", True),
            ("ESRS E1-4", "6", "Gross Scope 1 GHG emissions (tCO2e)", "numerical", True),
            ("ESRS E1-5", "7", "Gross Scope 2 location-based GHG emissions (tCO2e)", "numerical", True),
            ("ESRS E1-5", "8", "Gross Scope 2 market-based GHG emissions (tCO2e)", "numerical", True),
            ("ESRS E1-6", "9", "Gross Scope 3 GHG emissions (tCO2e)", "numerical", True),
            ("ESRS E1-6", "10", "Total GHG emissions (tCO2e)", "numerical", True),
            ("ESRS E1-7", "11", "GHG intensity per net revenue (tCO2e/EUR)", "numerical", True),
            ("ESRS E1-8", "12", "GHG emission reduction targets", "narrative", True),
            ("ESRS E1-8", "13", "Carbon credits and offsetting", "narrative", False),
            ("ESRS E1-9", "14", "Internal carbon pricing", "narrative", False),
            # E2 Pollution
            ("ESRS E2-1", "15", "Pollution management policy", "narrative", True),
            ("ESRS E2-2", "16", "Air pollutant emissions (kg)", "numerical", True),
            ("ESRS E2-3", "17", "Water pollution discharges", "numerical", True),
            ("ESRS E2-4", "18", "Substances of concern (tonnes)", "numerical", True),
            ("ESRS E2-5", "19", "Microplastics generated", "numerical", False),
            # E3 Water
            ("ESRS E3-1", "20", "Water management policy", "narrative", True),
            ("ESRS E3-2", "21", "Water consumption (m³)", "numerical", True),
            ("ESRS E3-3", "22", "Water intensity per revenue (m³/EUR)", "numerical", True),
            ("ESRS E3-4", "23", "Water discharge quality", "narrative", True),
            # E4 Biodiversity
            ("ESRS E4-1", "24", "Biodiversity policy", "narrative", True),
            ("ESRS E4-2", "25", "Sites near biodiversity-sensitive areas", "narrative", True),
            ("ESRS E4-3", "26", "Land use change (hectares)", "numerical", True),
            # E5 Circular Economy
            ("ESRS E5-1", "27", "Circular economy policy", "narrative", True),
            ("ESRS E5-2", "28", "Material inflows (tonnes)", "numerical", True),
            ("ESRS E5-3", "29", "Material outflows - waste (tonnes)", "numerical", True),
            ("ESRS E5-4", "30", "Waste diverted from disposal (tonnes)", "numerical", True),
            ("ESRS E5-5", "31", "Waste intensity per revenue", "numerical", True),
            # Social - S1 Own Workforce
            ("ESRS S1-1", "32", "Workforce characteristics", "narrative", True),
            ("ESRS S1-2", "33", "Number of employees (headcount)", "numerical", True),
            ("ESRS S1-3", "34", "Employee turnover rate (%)", "numerical", True),
            ("ESRS S1-4", "35", "Collective bargaining coverage (%)", "numerical", True),
            ("ESRS S1-5", "36", "Gender diversity in management (%)", "numerical", True),
            ("ESRS S1-6", "37", "Health and safety incidents", "numerical", True),
            ("ESRS S1-7", "38", "Training hours per employee", "numerical", True),
            ("ESRS S1-8", "39", "Work-life balance measures", "narrative", True),
            # S2 Value Chain Workers
            ("ESRS S2-1", "40", "Value chain worker assessment", "narrative", True),
            ("ESRS S2-2", "41", "Forced labor risk assessment", "narrative", True),
            # S3 Communities
            ("ESRS S3-1", "42", "Community impact assessment", "narrative", True),
            ("ESRS S3-2", "43", "Local hiring practices", "narrative", True),
            # S4 Consumers
            ("ESRS S4-1", "44", "Consumer health and safety", "narrative", True),
            ("ESRS S4-2", "45", "Privacy and data protection", "narrative", True),
            # Governance G1
            ("ESRS G1-1", "46", "Corporate culture and ethics", "narrative", True),
            ("ESRS G1-2", "47", "Anti-corruption policy", "narrative", True),
            ("ESRS G1-3", "48", "Whistleblower mechanism", "narrative", True),
            ("ESRS G1-4", "49", "Political engagement", "narrative", True),
            ("ESRS G1-5", "50", "Supplier payment practices (days)", "numerical", True),
        ]

        count = 0
        for std_ref, para, desc, dtype, mandatory in synthetic_data:
            existing = db.query(EsrsDatapoint).filter(
                EsrsDatapoint.standard_ref == std_ref,
                EsrsDatapoint.paragraph_ref == para,
            ).first()
            if not existing:
                db.add(EsrsDatapoint(
                    standard_ref=std_ref,
                    paragraph_ref=para,
                    disclosure_requirement=desc,
                    data_type=dtype,
                    is_mandatory=mandatory,
                ))
                count += 1

        db.commit()
        print(f"✅ Generated {count} synthetic ESRS datapoints.")


def _run_gap_analysis(company_id: str):
    """Run gap analysis for a given company."""
    from esrs_parser.gap_analyzer import GapAnalyzer

    print(f"🔍 Running gap analysis for company {company_id}...")
    db = _get_session()
    try:
        analyzer = GapAnalyzer(db)
        result = analyzer.get_summary(company_id)
        print(f"\n📊 Gap Analysis Results:")
        print(f"   Total Required: {result['total_required']}")
        print(f"   Complete: {result['complete']}")
        print(f"   Partial: {result['partial']}")
        print(f"   Missing: {result['missing']}")
        print(f"   Completion: {result['completion_percentage']}%")
        if result['priority_actions']:
            print(f"\n   Priority Actions:")
            for action in result['priority_actions'][:5]:
                print(f"   🔴 [{action['priority'].upper()}] {action['datapoint']}")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()


def _run_generate_iros(company_id: str, use_ai: bool = False):
    """Generate IROs for a company."""
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
    from ai_engine.materiality_engine.iro_generator import IROGenerator

    print(f"🎯 Generating IROs for company {company_id}...")
    if use_ai:
        print("   🤖 Using AI generation mode")

    db = _get_session()
    try:
        from backend.app.models import Company, CompanyContext

        company = db.query(Company).filter(
            Company.company_id == company_id
        ).first()
        if not company:
            print(f"❌ Company {company_id} not found")
            return

        context = db.query(CompanyContext).filter(
            CompanyContext.company_id == company_id
        ).first()

        context_dict = None
        if context:
            context_dict = {
                "value_chain": context.value_chain_description,
                "key_activities": context.key_activities or [],
                "geographical_scope": context.geographical_scope or [],
                "stakeholder_groups": context.stakeholder_groups or [],
            }

        iros = IROGenerator.generate_iros_for_company(
            company_sector=company.sector,
            employee_count=company.employee_count,
            turnover=company.turnover,
            company_context=context_dict,
            use_ai=use_ai,
        )
        summary = IROGenerator.get_summary(iros)

        print(f"\n📊 IRO Generation Results:")
        print(f"   Total IROs: {summary['total_iros']}")
        print(f"   By Type: {summary['by_type']}")
        print(f"   By Topic: {summary['by_topic']}")
        print(f"   Material: {summary['material_count']}")
        print(f"   AI Generated: {summary['ai_generated']}")

        print(f"\n   IRO List:")
        for iro in iros[:10]:
            mat = "🟢" if iro.get('is_material') else "⚪"
            ai_tag = "🤖" if iro.get('ai_generated') else "  "
            print(f"   {mat}{ai_tag} [{iro['type']:>12}] {iro['topic']:8} | {iro['name'][:60]}")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


def _run_questionnaire(company_id: str, sector_code: str):
    """Display questionnaire for a company's sector."""
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

    print(f"📋 Loading questionnaire for sector {sector_code}...")
    from backend.app.services.context_questionnaire import ContextQuestionnaireService

    questions = ContextQuestionnaireService.get_all_questions(sector_code)

    for phase in questions.get("phases", []):
        print(f"\n📌 Fase {phase['id']}: {phase['name']} ({phase['type']})")
        print(f"   {phase['description']}")
        for q in phase.get("questions", []):
            print(f"   ❓ {q['question']}")
            for opt in q.get('options', []):
                print(f"      • {opt}")
            print(f"      ESRS: {', '.join(q.get('esrs_topics', []))}")

    if questions.get("ai_generated_questions"):
        print(f"\n🤖 AI Questions:")
        for q in questions["ai_generated_questions"]:
            print(f"   • {q}")


def _run_gap_analysis(company_id: str):
    """Run gap analysis for a given company."""
    from esrs_parser.gap_analyzer import GapAnalyzer

    print(f"🔍 Running gap analysis for company {company_id}...")
    db = _get_session()
    try:
        analyzer = GapAnalyzer(db)
        result = analyzer.get_summary(company_id)
        print(f"\n📊 Gap Analysis Results:")
        print(f"   Total Required: {result['total_required']}")
        print(f"   Complete: {result['complete']}")
        print(f"   Partial: {result['partial']}")
        print(f"   Missing: {result['missing']}")
        print(f"   Completion: {result['completion_percentage']}%")
        if result['priority_actions']:
            print(f"\n   Priority Actions:")
            for action in result['priority_actions'][:5]:
                print(f"   🔴 [{action['priority'].upper()}] {action['datapoint']}")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
