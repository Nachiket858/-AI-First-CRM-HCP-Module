from database import Base, engine, SessionLocal
from models import HCP, Material, Sample, Interaction
import datetime

def seed_database():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # Check if database is already seeded
        if db.query(HCP).first() is not None:
            print("Database already seeded.")
            return

        print("Seeding database...")

        # 1. Seed HCPs
        hcps = [
            HCP(
                name="Dr. Sarah Jenkins",
                specialty="Cardiology",
                clinic="Apex Heart & Vascular Clinic",
                contact_number="+1-555-019-2834",
                email="sarah.jenkins@apexheart.com",
                preferences="Prefers clinical study summaries over promotional brochures. Prefers email follow-ups."
            ),
            HCP(
                name="Dr. Robert Chen",
                specialty="Oncology",
                clinic="Metro Cancer Center",
                contact_number="+1-555-014-9821",
                email="robert.chen@metrocancer.org",
                preferences="Interested in patient support programs and co-pay assistance information. Best visited in the morning."
            ),
            HCP(
                name="Dr. Emily Taylor",
                specialty="Pediatrics",
                clinic="Sunnyside Kids Clinic",
                contact_number="+1-555-012-4433",
                email="emily.taylor@sunnyside.com",
                preferences="Requires physical handouts for patients. Very busy on Tuesdays."
            ),
            HCP(
                name="Dr. James Wilson",
                specialty="Neurology",
                clinic="Brain & Nerve Specialists",
                contact_number="+1-555-018-7711",
                email="james.wilson@neurologyinst.com",
                preferences="Prefers visual slides or digital presentations. Keen on updates regarding clinical trial phase-3 for Alzheimers."
            )
        ]
        db.add_all(hcps)
        db.commit()

        # Retrieve saved HCPs for reference mapping
        jenkins = db.query(HCP).filter_by(name="Dr. Sarah Jenkins").first()
        chen = db.query(HCP).filter_by(name="Dr. Robert Chen").first()

        # 2. Seed Materials
        materials = [
            Material(name="Prodo-X Clinical Trial Summary", type="Clinical Trial", file_size="2.4 MB", url="https://crm-docs.life-sciences.com/prodo-x-clinical-trial.pdf"),
            Material(name="Prodo-X Dosage & Administration Brochure", type="Brochure", file_size="1.1 MB", url="https://crm-docs.life-sciences.com/prodo-x-dosage-brochure.pdf"),
            Material(name="Prodo-X Efficacy & Patient Outcomes Sheet", type="Product Brief", file_size="850 KB", url="https://crm-docs.life-sciences.com/prodo-x-efficacy.pdf"),
            Material(name="CardioPlus Efficacy Sheet", type="Product Brief", file_size="920 KB", url="https://crm-docs.life-sciences.com/cardioplus-efficacy.pdf"),
            Material(name="CardioPlus Patient Care Pamphlet", type="Brochure", file_size="1.5 MB", url="https://crm-docs.life-sciences.com/cardioplus-patient-pamphlet.pdf")
        ]
        db.add_all(materials)

        # 3. Seed Samples
        samples = [
            Sample(name="Prodo-X 5mg Starter Pack", description="Starter pack with 10 daily doses of Prodo-X 5mg."),
            Sample(name="Prodo-X 10mg Trial Kit", description="Sample card with 5 trial tablets of Prodo-X 10mg."),
            Sample(name="CardioPlus 20mg Sample Bottle", description="Sample bottle with 30 tablets of CardioPlus 20mg.")
        ]
        db.add_all(samples)
        db.commit()

        # 4. Seed Past Interactions
        past_interactions = [
            Interaction(
                hcp_id=jenkins.id,
                interaction_type="Meeting",
                date="2026-06-15",
                time="10:30 AM",
                attendees="Dr. Sarah Jenkins, Rep John Doe",
                topics_discussed="Initial interest in Prodo-X for cardiovascular outcomes. Discussed comparative safety profile against standard care.",
                sentiment="Positive",
                outcomes="Dr. Jenkins requested clinical trial summaries. She expressed potential interest in recommending it to patients with moderate risk.",
                follow_up_actions="Send the Prodo-X Clinical Trial Summary via email and follow up during the next clinic visit.",
                status="Logged"
            ),
            Interaction(
                hcp_id=chen.id,
                interaction_type="Call",
                date="2026-06-28",
                time="09:15 AM",
                attendees="Dr. Robert Chen, Rep John Doe",
                topics_discussed="Brief call regarding oncology oncology-support patient co-pay cards. Shared brief updates.",
                sentiment="Neutral",
                outcomes="Dr. Chen asked to receive co-pay brochures next time the representative visits in person.",
                follow_up_actions="Deliver co-pay physical materials during the next visit.",
                status="Logged"
            )
        ]
        db.add_all(past_interactions)
        db.commit()

        print("Seeding completed successfully.")
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
