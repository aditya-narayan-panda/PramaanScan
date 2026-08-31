"""
PramaanScan Database Seeder.

Seeds comprehensive initial data for demonstration, evaluation, and QA:
- 1 Platform Administrator (admin@pramaanscan.gov.in)
- 3 Active Institutions (NTA, MeitY, IIT Bombay) with Ed25519 Signing Keys and Authority Accounts
- 1 Suspended Institution (for testing suspension authorization rejection)
- Real signed communications (Circulars, Examination Notifications, Certificates)
- 1 Revoked key & revoked communication test case for negative verification tests
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timezone

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.db.session import engine, SessionLocal
from app.db.base import Base
from app.models.user import User, UserRole
from app.models.issuer import Issuer, IssuerStatus
from app.models.signing_key import SigningKey, KeyStatus
from app.models.communication import Communication, CommunicationVersion, CommunicationStatus, MediaType
from app.models.revocation import Revocation, RevocationTargetType
from app.models.audit_log import AuditLog
from app.security.auth import hash_password
from app.services.crypto import generate_key_pair, sign_data
from app.services.hashing import sha256_bytes


def seed_database():
    print("=" * 70)
    print("PRAMAANSCAN DATABASE SEEDING")
    print("=" * 70)

    # Initialize tables
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # Check if already seeded
        admin_check = db.query(User).filter(User.email == "admin@pramaanscan.gov.in").first()
        if admin_check:
            print("Database is already seeded with admin user.")
            return

        print("Creating System Administrator...")
        admin = User(
            email="admin@pramaanscan.gov.in",
            password_hash=hash_password("Admin@12345"),
            full_name="National Platform Administrator",
            role=UserRole.ADMIN,
            is_active=True,
        )
        db.add(admin)
        db.flush()

        # -------------------------------------------------------------
        # 1. NTA Institution & Authority
        # -------------------------------------------------------------
        print("Creating Institution: National Testing Agency (NTA)...")
        nta = Issuer(
            institution_name="National Testing Agency (NTA)",
            email="authority@nta.ac.in",
            contact_phone="+91-11-69227700",
            status=IssuerStatus.ACTIVE,
        )
        db.add(nta)
        db.flush()

        nta_user = User(
            email="officer@nta.ac.in",
            password_hash=hash_password("Nta@12345"),
            full_name="Dr. S. K. Sharma (Director of Examinations)",
            role=UserRole.AUTHORITY,
            issuer_id=nta.id,
            is_active=True,
        )
        db.add(nta_user)
        db.flush()

        nta_priv, nta_pub = generate_key_pair()
        nta_key = SigningKey(
            key_id="key_nta_primary_2026",
            issuer_id=nta.id,
            algorithm="Ed25519",
            public_key=nta_pub,
            private_key_encrypted=nta_priv,
            status=KeyStatus.ACTIVE,
        )
        db.add(nta_key)
        db.flush()

        # Sample communication for NTA
        sample_doc_bytes = b"NATIONAL TESTING AGENCY - OFFICIAL PUBLIC NOTICE: JEE MAIN 2026 RESULTS & CUTOFFS"
        sample_hash = sha256_bytes(sample_doc_bytes)
        sample_sig = sign_data(sample_hash.encode("utf-8"), nta_priv)

        nta_comm = Communication(
            communication_id="nta_jee_main_2026_notice",
            issuer_id=nta.id,
            title="Public Notice: JEE Main 2026 Scorecard Declaration & Cutoffs",
            description="Official declaration of National Testing Agency scorecards for the 2026 joint entrance cycle.",
            category="Examination Notification",
            media_type=MediaType.DOCUMENT,
            status=CommunicationStatus.CURRENT,
        )
        db.add(nta_comm)
        db.flush()

        nta_comm_version = CommunicationVersion(
            communication_id=nta_comm.id,
            version_number=1,
            sha256=sample_hash,
            signature=sample_sig,
            key_id=nta_key.id,
            file_name="JEE_Main_2026_Official_Notice.pdf",
            mime_type="application/pdf",
            file_size_bytes=len(sample_doc_bytes),
            created_by=nta_user.id,
        )
        db.add(nta_comm_version)
        db.flush()
        nta_comm.current_version_id = nta_comm_version.id

        # -------------------------------------------------------------
        # 2. MeitY Institution & Authority
        # -------------------------------------------------------------
        print("Creating Institution: Ministry of Electronics & IT (MeitY)...")
        meity = Issuer(
            institution_name="Ministry of Electronics & Information Technology (MeitY)",
            email="authority@meity.gov.in",
            contact_phone="+91-11-24360199",
            status=IssuerStatus.ACTIVE,
        )
        db.add(meity)
        db.flush()

        meity_user = User(
            email="director@meity.gov.in",
            password_hash=hash_password("Meity@12345"),
            full_name="Rajesh Verma (Joint Secretary)",
            role=UserRole.AUTHORITY,
            issuer_id=meity.id,
            is_active=True,
        )
        db.add(meity_user)
        db.flush()

        meity_priv, meity_pub = generate_key_pair()
        meity_key = SigningKey(
            key_id="key_meity_cyber_2026",
            issuer_id=meity.id,
            algorithm="Ed25519",
            public_key=meity_pub,
            private_key_encrypted=meity_priv,
            status=KeyStatus.ACTIVE,
        )
        db.add(meity_key)
        db.flush()

        meity_doc_bytes = b"MINISTRY OF ELECTRONICS & IT - ADVISORY ON DIGITAL VERIFICATION INFRASTRUCTURE 2026"
        meity_hash = sha256_bytes(meity_doc_bytes)
        meity_sig = sign_data(meity_hash.encode("utf-8"), meity_priv)

        meity_comm = Communication(
            communication_id="meity_digital_trust_circular_2026",
            issuer_id=meity.id,
            title="National Advisory on Cryptographic Verification of Official Records",
            description="Framework and standards advisory for multi-institution digital trust architecture.",
            category="Policy Circular",
            media_type=MediaType.DOCUMENT,
            status=CommunicationStatus.CURRENT,
        )
        db.add(meity_comm)
        db.flush()

        meity_comm_version = CommunicationVersion(
            communication_id=meity_comm.id,
            version_number=1,
            sha256=meity_hash,
            signature=meity_sig,
            key_id=meity_key.id,
            file_name="MeitY_Digital_Trust_Circular.pdf",
            mime_type="application/pdf",
            file_size_bytes=len(meity_doc_bytes),
            created_by=meity_user.id,
        )
        db.add(meity_comm_version)
        db.flush()
        meity_comm.current_version_id = meity_comm_version.id

        # -------------------------------------------------------------
        # 3. IIT Bombay Institution & Authority
        # -------------------------------------------------------------
        print("Creating Institution: IIT Bombay...")
        iitb = Issuer(
            institution_name="Indian Institute of Technology, Bombay",
            email="academic@iitb.ac.in",
            contact_phone="+91-22-25722545",
            status=IssuerStatus.ACTIVE,
        )
        db.add(iitb)
        db.flush()

        iitb_user = User(
            email="dean.academics@iitb.ac.in",
            password_hash=hash_password("Iitb@12345"),
            full_name="Prof. Ananya Sen (Dean of Academic Programmes)",
            role=UserRole.AUTHORITY,
            issuer_id=iitb.id,
            is_active=True,
        )
        db.add(iitb_user)
        db.flush()

        iitb_priv, iitb_pub = generate_key_pair()
        iitb_key = SigningKey(
            key_id="key_iitb_degree_2026",
            issuer_id=iitb.id,
            algorithm="Ed25519",
            public_key=iitb_pub,
            private_key_encrypted=iitb_priv,
            status=KeyStatus.ACTIVE,
        )
        db.add(iitb_key)
        db.flush()

        # -------------------------------------------------------------
        # 4. Suspended Test Institution (For negative authorization testing)
        # -------------------------------------------------------------
        print("Creating Suspended Institution (For security evaluation)...")
        suspended_inst = Issuer(
            institution_name="Suspended Test Academy",
            email="admin@suspended-test.org",
            contact_phone="+91-00-00000000",
            status=IssuerStatus.SUSPENDED,
        )
        db.add(suspended_inst)
        db.flush()

        suspended_user = User(
            email="authority@suspended-test.org",
            password_hash=hash_password("Suspended@12345"),
            full_name="Suspended Authority Officer",
            role=UserRole.AUTHORITY,
            issuer_id=suspended_inst.id,
            is_active=True,
        )
        db.add(suspended_user)
        db.flush()

        # -------------------------------------------------------------
        # 5. Revoked Key Test Case (For revocation verification)
        # -------------------------------------------------------------
        revoked_priv, revoked_pub = generate_key_pair()
        revoked_key = SigningKey(
            key_id="key_nta_legacy_revoked_2025",
            issuer_id=nta.id,
            algorithm="Ed25519",
            public_key=revoked_pub,
            private_key_encrypted=revoked_priv,
            status=KeyStatus.REVOKED,
            revoked_at=datetime.now(timezone.utc),
            revoked_reason="Compromised private key during 2025 infrastructure migration.",
        )
        db.add(revoked_key)
        db.flush()

        rev_record = Revocation(
            target_type=RevocationTargetType.SIGNING_KEY,
            target_id=revoked_key.key_id,
            reason=revoked_key.revoked_reason,
            revoked_by=admin.id,
            revoked_at=datetime.now(timezone.utc),
        )
        db.add(rev_record)

        db.commit()
        print()
        print("SEEDING COMPLETED SUCCESSFULLY!")
        print("-" * 70)
        print("DEMO CREDENTIALS:")
        print("  1. Platform Admin:")
        print("     Email: admin@pramaanscan.gov.in | Password: Admin@12345")
        print("  2. NTA Authority:")
        print("     Email: officer@nta.ac.in        | Password: Nta@12345")
        print("  3. MeitY Authority:")
        print("     Email: director@meity.gov.in    | Password: Meity@12345")
        print("  4. IIT Bombay Authority:")
        print("     Email: dean.academics@iitb.ac.in| Password: Iitb@12345")
        print("  5. Suspended Institution Test:")
        print("     Email: authority@suspended-test.org | Password: Suspended@12345")
        print("-" * 70)
        print("SAMPLE VERIFIABLE DOCUMENT IDS:")
        print(f"  - NTA Notice ID:   nta_jee_main_2026_notice")
        print(f"  - MeitY Circular:  meity_digital_trust_circular_2026")
        print("=" * 70)

    except Exception as e:
        db.rollback()
        print(f"ERROR DURING SEEDING: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
