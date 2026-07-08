from database import Base, engine, SessionLocal
from models import HCP, Material, Sample, Interaction
import datetime

def seed_database():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # 1. Seed HCPs
        hcps = [
            HCP(
                name="Dr. Amit Sharma",
                specialty="Cardiology",
                clinic="Apex Heart Clinic",
                contact_number="+91-98765-43210",
                email="amit.sharma@apexheart.in",
                preferences="Prefers clinical study summaries over promotional brochures. Prefers email follow-ups."
            ),
            HCP(
                name="Dr. Priya Patel",
                specialty="Oncology",
                clinic="Metro Cancer Care Center",
                contact_number="+91-87654-32109",
                email="priya.patel@metrocancer.org.in",
                preferences="Interested in patient support programs and co-pay assistance information. Best visited in the morning."
            ),
            HCP(
                name="Dr. Rohan Gupta",
                specialty="Pediatrics",
                clinic="Sunnyside Kids Clinic",
                contact_number="+91-76543-21098",
                email="rohan.gupta@sunnyside.in",
                preferences="Requires physical handouts for patients. Very busy on Tuesdays."
            ),
            HCP(
                name="Dr. Suresh Verma",
                specialty="Neurology",
                clinic="Brain Care Specialists",
                contact_number="+91-65432-10987",
                email="suresh.verma@neurologyinst.in",
                preferences="Prefers visual slides or digital presentations. Keen on updates regarding clinical trial phase-3 for Alzheimers."
            )
        ]
        for h in hcps:
            if not db.query(HCP).filter_by(name=h.name).first():
                db.add(h)
        db.commit()

        # Retrieve saved HCPs for reference mapping
        sharma = db.query(HCP).filter_by(name="Dr. Amit Sharma").first()
        patel = db.query(HCP).filter_by(name="Dr. Priya Patel").first()

        # 2. Seed Materials
        materials = [
            Material(name="Prodo-X Clinical Trial Summary", type="Clinical Trial", file_size="2.4 MB", url="https://crm-docs.life-sciences.com/prodo-x-clinical-trial.pdf"),
            Material(name="Prodo-X Dosage & Administration Brochure", type="Brochure", file_size="1.1 MB", url="https://crm-docs.life-sciences.com/prodo-x-dosage-brochure.pdf"),
            Material(name="Prodo-X Efficacy & Patient Outcomes Sheet", type="Product Brief", file_size="850 KB", url="https://crm-docs.life-sciences.com/prodo-x-efficacy.pdf"),
            Material(name="CardioPlus Efficacy Sheet", type="Product Brief", file_size="920 KB", url="https://crm-docs.life-sciences.com/cardioplus-efficacy.pdf"),
            Material(name="CardioPlus Patient Care Pamphlet", type="Brochure", file_size="1.5 MB", url="https://crm-docs.life-sciences.com/cardioplus-patient-pamphlet.pdf")
        ]
        for m in materials:
            if not db.query(Material).filter_by(name=m.name).first():
                db.add(m)
        db.commit()

        # 3. Seed Samples
        samples = [
            Sample(name="Prodo-X 5mg Starter Pack", description="Starter pack with 10 daily doses of Prodo-X 5mg."),
            Sample(name="Prodo-X 10mg Trial Kit", description="Sample card with 5 trial tablets of Prodo-X 10mg."),
            Sample(name="CardioPlus 20mg Sample Bottle", description="Sample bottle with 30 tablets of CardioPlus 20mg.")
        ]
        for s in samples:
            if not db.query(Sample).filter_by(name=s.name).first():
                db.add(s)
        db.commit()

        # 4. Seed Past Interactions
        past_interactions = [
            Interaction(
                hcp_id=sharma.id if sharma else 1,
                interaction_type="Meeting",
                date="2026-06-15",
                time="10:30 AM",
                attendees="Dr. Amit Sharma, Rep John Doe",
                topics_discussed="Initial interest in Prodo-X for cardiovascular outcomes. Discussed comparative safety profile against standard care.",
                sentiment="Positive",
                outcomes="Dr. Sharma requested clinical trial summaries. She expressed potential interest in recommending it to patients with moderate risk.",
                follow_up_actions="Send the Prodo-X Clinical Trial Summary via email and follow up during the next clinic visit.",
                status="Logged"
            ),
            Interaction(
                hcp_id=patel.id if patel else 2,
                interaction_type="Call",
                date="2026-06-28",
                time="09:15 AM",
                attendees="Dr. Priya Patel, Rep John Doe",
                topics_discussed="Brief call regarding oncology oncology-support patient co-pay cards. Shared brief updates.",
                sentiment="Neutral",
                outcomes="Dr. Patel asked to receive co-pay brochures next time the representative visits in person.",
                follow_up_actions="Deliver co-pay physical materials during the next visit.",
                status="Logged"
            )
        ]
        if db.query(Interaction).first() is None:
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
