"""Seed the database with sample Nigerian election data for development/testing.

This script populates the database with:
- Election types (Presidential, Governorship, etc.)
- Political parties (APC, PDP, LP, etc.)
- Geographic hierarchy (States → LGAs → Wards → Polling Units)
- Election results with party vote counts

Run: cd backend && source .venv/bin/activate && python seed_data.py
"""
from __future__ import annotations

import asyncio
import random
from decimal import Decimal

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings
from app.models.election import ElectionResult, ElectionType, PartyResult, PoliticalParty
from app.models.geography import LGA, PollingUnit, State, Ward

settings = get_settings()

engine = create_async_engine(settings.database.async_url, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# --- Reference data ---

ELECTION_TYPES = [
    ("Presidential Election", "presidential"),
    ("Governorship Election", "governorship"),
    ("Senatorial Election", "senatorial"),
    ("House of Representatives", "house-of-reps"),
    ("State House of Assembly", "state-assembly"),
]

PARTIES = [
    ("All Progressives Congress", "APC"),
    ("Peoples Democratic Party", "PDP"),
    ("Labour Party", "LP"),
    ("New Nigeria Peoples Party", "NNPP"),
    ("All Progressives Grand Alliance", "APGA"),
    ("African Democratic Congress", "ADC"),
    ("Social Democratic Party", "SDP"),
    ("Young Progressives Party", "YPP"),
    ("Zenith Labour Party", "ZLP"),
    ("Action Alliance", "AA"),
    ("African Action Congress", "AAC"),
    ("Peoples Redemption Party", "PRP"),
    ("Accord Party", "ACCORD"),
    ("Action Democratic Party", "ADP"),
    ("Boot Party", "BP"),
    ("National Rescue Movement", "NRM"),
]

# Subset of Nigerian states with LGAs, wards, and polling units
# Using real names for realism
STATES_DATA = {
    "Lagos": {
        "code": "lagos",
        "lgas": {
            "Ikeja": {
                "code": "ikeja",
                "wards": [
                    ("Alausa", "alausa", 8),
                    ("Anifowoshe", "anifowoshe", 6),
                    ("GRA", "gra", 5),
                    ("Onigbongbo", "onigbongbo", 7),
                    ("Ojodu", "ojodu", 9),
                ],
            },
            "Eti-Osa": {
                "code": "eti-osa",
                "wards": [
                    ("Lekki", "lekki", 10),
                    ("Victoria Island", "vi", 6),
                    ("Ikoyi", "ikoyi", 5),
                    ("Ajah", "ajah", 12),
                ],
            },
            "Surulere": {
                "code": "surulere",
                "wards": [
                    ("Aguda", "aguda", 7),
                    ("Coker", "coker", 6),
                    ("Itire", "itire", 8),
                    ("Iponri", "iponri", 5),
                ],
            },
        },
    },
    "Kano": {
        "code": "kano",
        "lgas": {
            "Kano Municipal": {
                "code": "kano-municipal",
                "wards": [
                    ("Fagge", "fagge", 10),
                    ("Gwale", "gwale", 8),
                    ("Nassarawa", "nassarawa", 7),
                    ("Tarauni", "tarauni", 9),
                ],
            },
            "Dala": {
                "code": "dala",
                "wards": [
                    ("Kantudu", "kantudu", 6),
                    ("Gwammaja", "gwammaja", 7),
                    ("Dogon Dutse", "dogon-dutse", 5),
                ],
            },
            "Ungogo": {
                "code": "ungogo",
                "wards": [
                    ("Ungogo Central", "ungogo-central", 8),
                    ("Rangaza", "rangaza", 6),
                    ("Rijiyar Zaki", "rijiyar-zaki", 7),
                ],
            },
        },
    },
    "Rivers": {
        "code": "rivers",
        "lgas": {
            "Port Harcourt": {
                "code": "port-harcourt",
                "wards": [
                    ("Diobu", "diobu", 9),
                    ("Nkpolu", "nkpolu", 7),
                    ("Rumuola", "rumuola", 6),
                    ("Rumuomasi", "rumuomasi", 8),
                ],
            },
            "Obio-Akpor": {
                "code": "obio-akpor",
                "wards": [
                    ("Rumuokwurushi", "rumuokwurushi", 10),
                    ("Choba", "choba", 7),
                    ("Elelenwo", "elelenwo", 8),
                ],
            },
        },
    },
    "FCT": {
        "code": "fct",
        "lgas": {
            "Abuja Municipal": {
                "code": "abuja-municipal",
                "wards": [
                    ("Wuse", "wuse", 8),
                    ("Garki", "garki", 7),
                    ("Maitama", "maitama", 5),
                    ("Asokoro", "asokoro", 6),
                    ("Gwarinpa", "gwarinpa", 10),
                ],
            },
            "Bwari": {
                "code": "bwari",
                "wards": [
                    ("Bwari Central", "bwari-central", 6),
                    ("Kuduru", "kuduru", 5),
                    ("Ushafa", "ushafa", 4),
                ],
            },
        },
    },
    "Anambra": {
        "code": "anambra",
        "lgas": {
            "Awka South": {
                "code": "awka-south",
                "wards": [
                    ("Amawbia", "amawbia", 7),
                    ("Nibo", "nibo", 5),
                    ("Nise", "nise", 6),
                    ("Mbaukwu", "mbaukwu", 4),
                ],
            },
            "Onitsha North": {
                "code": "onitsha-north",
                "wards": [
                    ("Onitsha Central", "onitsha-central", 8),
                    ("Inland Town", "inland-town", 6),
                    ("Waterside", "waterside", 5),
                ],
            },
        },
    },
    "Oyo": {
        "code": "oyo",
        "lgas": {
            "Ibadan North": {
                "code": "ibadan-north",
                "wards": [
                    ("Bodija", "bodija", 9),
                    ("Sango", "sango", 7),
                    ("Agodi", "agodi", 6),
                    ("Oke-Itunu", "oke-itunu", 8),
                ],
            },
            "Ibadan South-West": {
                "code": "ibadan-sw",
                "wards": [
                    ("Oluyole", "oluyole", 7),
                    ("Ring Road", "ring-road", 6),
                    ("Challenge", "challenge", 8),
                ],
            },
        },
    },
}


def generate_votes(num_parties: int, accredited: int) -> list[int]:
    """Generate realistic vote distribution for parties."""
    # Top 3-4 parties get most votes, rest get small amounts
    total_valid = int(accredited * random.uniform(0.75, 0.95))
    votes = []

    # Major parties get larger shares
    remaining = total_valid
    for i in range(num_parties):
        if i == 0:
            v = int(remaining * random.uniform(0.25, 0.45))
        elif i == 1:
            v = int(remaining * random.uniform(0.20, 0.35))
        elif i == 2:
            v = int(remaining * random.uniform(0.10, 0.25))
        elif i < 5:
            v = int(remaining * random.uniform(0.02, 0.08))
        else:
            v = random.randint(0, max(1, int(remaining * 0.02)))
        votes.append(v)
        remaining -= v
        if remaining <= 0:
            votes.extend([0] * (num_parties - len(votes)))
            break

    # Ensure no negatives
    votes = [max(0, v) for v in votes]
    return votes


async def seed():
    """Seed the database with sample data."""
    async with async_session() as session:
        # Check if data already exists
        result = await session.execute(text("SELECT count(*) FROM election_types"))
        count = result.scalar()
        if count and count > 0:
            print("Database already has data. Skipping seed.")
            return

        print("Seeding database...")

        # 1. Create election types
        election_type_objs: dict[str, ElectionType] = {}
        for name, code in ELECTION_TYPES:
            et = ElectionType(name=name, code=code)
            session.add(et)
            election_type_objs[code] = et
        await session.flush()
        print(f"  Created {len(ELECTION_TYPES)} election types")

        # 2. Create political parties
        party_objs: dict[str, PoliticalParty] = {}
        for name, code in PARTIES:
            p = PoliticalParty(name=name, code=code)
            session.add(p)
            party_objs[code] = p
        await session.flush()
        print(f"  Created {len(PARTIES)} political parties")

        # Main parties that appear in every result (top 6)
        main_party_codes = ["APC", "PDP", "LP", "NNPP", "APGA", "ADC", "SDP", "YPP"]

        # 3. Create geographic hierarchy and results
        total_pus = 0
        total_results = 0

        for state_name, state_data in STATES_DATA.items():
            state = State(
                name=state_name,
                code=state_data["code"],
                total_lgas=len(state_data["lgas"]),
            )
            session.add(state)
            await session.flush()

            for lga_name, lga_data in state_data["lgas"].items():
                lga = LGA(
                    state_id=state.id,
                    name=lga_name,
                    code=lga_data["code"],
                    total_wards=len(lga_data["wards"]),
                )
                session.add(lga)
                await session.flush()

                for ward_name, ward_code, num_pus in lga_data["wards"]:
                    ward = Ward(
                        lga_id=lga.id,
                        name=ward_name,
                        code=ward_code,
                        total_polling_units=num_pus,
                    )
                    session.add(ward)
                    await session.flush()

                    for pu_idx in range(1, num_pus + 1):
                        pu = PollingUnit(
                            ward_id=ward.id,
                            name=f"{ward_name} PU {pu_idx:03d}",
                            code=f"{ward_code}-{pu_idx:03d}",
                        )
                        session.add(pu)
                        await session.flush()
                        total_pus += 1

                        # Create election results for presidential and governorship
                        for et_code in ["presidential", "governorship"]:
                            et = election_type_objs[et_code]
                            accredited = random.randint(150, 600)
                            votes = generate_votes(len(main_party_codes), accredited)
                            valid_votes = sum(votes)
                            rejected = random.randint(2, max(3, int(accredited * 0.05)))
                            confidence = round(random.uniform(0.75, 0.98), 2)

                            er = ElectionResult(
                                election_type_id=et.id,
                                polling_unit_id=pu.id,
                                accredited_voters=accredited,
                                valid_votes=valid_votes,
                                rejected_votes=rejected,
                                confidence_score=Decimal(str(confidence)),
                                source_image_path=f"data/result_sheets/{state_data['code']}/{lga_data['code']}/{ward_code}/{pu.code}.png",
                            )
                            session.add(er)
                            await session.flush()
                            total_results += 1

                            # Create party results
                            for i, party_code in enumerate(main_party_codes):
                                if i < len(votes):
                                    vote_count = votes[i]
                                    pct = (
                                        round(vote_count / valid_votes * 100, 2)
                                        if valid_votes > 0
                                        else 0
                                    )
                                    pr = PartyResult(
                                        election_result_id=er.id,
                                        party_id=party_objs[party_code].id,
                                        vote_count=vote_count,
                                        percentage=Decimal(str(pct)),
                                    )
                                    session.add(pr)

        await session.commit()
        print(f"  Created {len(STATES_DATA)} states with LGAs, wards, and polling units")
        print(f"  Total polling units: {total_pus}")
        print(f"  Total election results: {total_results}")
        print("Seed complete!")


if __name__ == "__main__":
    asyncio.run(seed())
