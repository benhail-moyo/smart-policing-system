#!/usr/bin/env python3
"""
Seed 50 realistic crime incidents reflecting real-world crime patterns across Harare.

This script creates incidents that mirror actual crime statistics and patterns
observed in Harare, including:
- Residential break-ins and theft
- Street robbery and muggings
- Domestic disputes
- Drug-related offenses
- Vehicle theft
- Commercial crime
- Assault cases
- Fraud and cybercrime

Run from the repository root:
    python backend/scripts/seed_realistic_harare_incidents.py
"""
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app, db
from app.models.models import Incident, User


# Realistic Harare crime incidents reflecting actual patterns
REALISTIC_INCIDENTS = [
    # Residential Break-ins and Theft (high in suburbs)
    {
        "raw_text": "Break-in at my house in Mbare. Thieves stole TV, laptop, and cash. They broke the back door while we were at work.",
        "category": "theft",
        "severity": "HIGH",
        "location": (-17.8677, 31.0359),
        "area": "Mbare",
        "language": "en"
    },
    {
        "raw_text": "Hw many people kumba tsvina imba yekera humba dze ipapo nemwashers. (How many people, thieves entered my house and took iPhones and washing machines)",
        "category": "theft",
        "severity": "HIGH",
        "location": (-17.8650, 31.0380),
        "area": "Mbare",
        "language": "sn"
    },
    {
        "raw_text": "Suspicious people seen trying car doors in Avenues area. They might be looking for unlocked vehicles.",
        "category": "suspicious_activity",
        "severity": "MEDIUM",
        "location": (-17.8320, 31.0550),
        "area": "Avenues",
        "language": "en"
    },
    {
        "raw_text": "My car was broken into overnight in Belvedere. Radio and valuables stolen from the dashboard.",
        "category": "theft",
        "severity": "HIGH",
        "location": (-17.8150, 31.0450),
        "area": "Belvedere",
        "language": "en"
    },
    {
        "raw_text": "Someone attempted to snatch my phone while walking along Jason Moyo Avenue near Joina City.",
        "category": "robbery",
        "severity": "HIGH",
        "location": (-17.8290, 31.0510),
        "area": "CBD",
        "language": "en"
    },
    
    # Street Robbery and Muggings (common in high-traffic areas)
    {
        "raw_text": "Was robbed at knife point near Copacabana bus terminus. They took my phone and wallet.",
        "category": "robbery",
        "severity": "HIGH",
        "location": (-17.8250, 31.0475),
        "area": "CBD",
        "language": "en"
    },
    {
        "raw_text": "Group of young men harassing people near Fourth Street bus stop. demanding money and phones.",
        "category": "robbery",
        "severity": "HIGH",
        "location": (-17.8280, 31.0500),
        "area": "CBD",
        "language": "en"
    },
    {
        "raw_text": "Mugging incident reported along Samora Machel Avenue. Victim had bag snatched while walking.",
        "category": "robbery",
        "severity": "HIGH",
        "location": (-17.8220, 31.0480),
        "area": "CBD",
        "language": "en"
    },
    {
        "raw_text": "Phone snatcher targeting people leaving malls in Eastlea. They operate in groups.",
        "category": "theft",
        "severity": "MEDIUM",
        "location": (-17.8100, 31.0600),
        "area": "Eastlea",
        "language": "en"
    },
    
    # Domestic Disputes (common in residential areas)
    {
        "raw_text": "Loud argument and physical fight reported in Budiriro. Neighbors concerned about woman's safety.",
        "category": "domestic_dispute",
        "severity": "MEDIUM",
        "location": (-17.9100, 31.0200),
        "area": "Budiriro",
        "language": "en"
    },
    {
        "raw_text": "Man assaulting wife in Mufakose. Children screaming heard by neighbors.",
        "category": "assault",
        "severity": "HIGH",
        "location": (-17.9200, 31.0150),
        "area": "Mufakose",
        "language": "en"
    },
    {
        "raw_text": "Family dispute in Mabvuku turned violent. Husband threatening wife with a weapon.",
        "category": "domestic_dispute",
        "severity": "HIGH",
        "location": (-17.9000, 31.0800),
        "area": "Mabvuku",
        "language": "en"
    },
    {
        "raw_text": "Domestic violence case in Highfields. Woman seeking help from neighbors after being beaten.",
        "category": "assault",
        "severity": "HIGH",
        "location": (-17.8900, 31.0100),
        "area": "Highfields",
        "language": "en"
    },
    
    # Drug-Related Offenses (increasing in some areas)
    {
        "raw_text": "Suspicious drug dealing activity observed near open space in Mbare. Groups gathering late at night.",
        "category": "drug_offence",
        "severity": "MEDIUM",
        "location": (-17.8680, 31.0330),
        "area": "Mbare",
        "language": "en"
    },
    {
        "raw_text": "Youth smoking dagga openly in public park in Mabelreign. Groups causing nuisance to residents.",
        "category": "drug_offence",
        "severity": "LOW",
        "location": (-17.7958, 31.0289),
        "area": "Mabelreign",
        "language": "en"
    },
    {
        "raw_text": "Drug dealer arrested near shopping center in Chitungwiza. Large quantity of illicit substances recovered.",
        "category": "drug_offence",
        "severity": "HIGH",
        "location": (-18.0130, 31.0750),
        "area": "Chitungwiza",
        "language": "en"
    },
    {
        "raw_text": "Suspicious substances being sold near bars in Glen Norah. Police should investigate.",
        "category": "drug_offence",
        "severity": "MEDIUM",
        "location": (-17.7800, 31.0700),
        "area": "Glen Norah",
        "language": "en"
    },
    
    # Vehicle Theft and Hijacking
    {
        "raw_text": "Car hijacking attempt in borrowdale. Two men tried to force driver out of vehicle at traffic lights.",
        "category": "robbery",
        "severity": "HIGH",
        "location": (-17.7847, 31.0722),
        "area": "Borrowdale",
        "language": "en"
    },
    {
        "raw_text": "Vehicle theft reported in Sunningdale. Car parked overnight was stolen without trace.",
        "category": "theft",
        "severity": "HIGH",
        "location": (-17.7700, 31.0800),
        "area": "Sunningdale",
        "language": "en"
    },
    {
        "raw_text": "Motorcycle theft near Westgate Mall. Two thieves on another bike snatched parked motorcycle.",
        "category": "theft",
        "severity": "HIGH",
        "location": (-17.7500, 31.0900),
        "area": "Westgate",
        "language": "en"
    },
    {
        "raw_text": "Attempted car theft in Avondale. Thieves caught trying to break car door lock.",
        "category": "theft",
        "severity": "MEDIUM",
        "location": (-17.7600, 31.0500),
        "area": "Avondale",
        "language": "en"
    },
    
    # Commercial Crime
    {
        "raw_text": "Shop breaking reported in Harare CBD. Thieves smashed display case and stole high-value goods.",
        "category": "theft",
        "severity": "HIGH",
        "location": (-17.8292, 31.0522),
        "area": "CBD",
        "language": "en"
    },
    {
        "raw_text": "Fraud case involving fake currency exchange in city center. Victim lost significant amount of money.",
        "category": "fraud",
        "severity": "HIGH",
        "location": (-17.8270, 31.0530),
        "area": "CBD",
        "language": "en"
    },
    {
        "raw_text": "Business email compromise reported. Company lost funds through fraudulent bank transfer instructions.",
        "category": "fraud",
        "severity": "HIGH",
        "location": (-17.8260, 31.0510),
        "area": "CBD",
        "language": "en"
    },
    {
        "raw_text": "Shoplifting incident at grocery store in Sam Levy Village. Security caught suspect red-handed.",
        "category": "theft",
        "severity": "LOW",
        "location": (-17.8400, 31.0400),
        "area": "Sam Levy Village",
        "language": "en"
    },
    
    # Assault Cases
    {
        "raw_text": "Bar fight turned violent in Mbare. One person seriously injured, bottles used as weapons.",
        "category": "assault",
        "severity": "HIGH",
        "location": (-17.8660, 31.0370),
        "area": "Mbare",
        "language": "en"
    },
    {
        "raw_text": "Assault with a dangerous weapon reported in Highfields. Victim hospitalized with serious injuries.",
        "category": "assault",
        "severity": "HIGH",
        "location": (-17.8920, 31.0080),
        "area": "Highfields",
        "language": "en"
    },
    {
        "raw_text": "Group fight at a shebeen in Dzivarasekwa. Multiple injuries reported, police intervened.",
        "category": "assault",
        "severity": "MEDIUM",
        "location": (-17.8800, 31.0950),
        "area": "Dzivarasekwa",
        "language": "en"
    },
    {
        "raw_text": "Person assaulted during robbery attempt in Chitungwiza. Victim injured during struggle.",
        "category": "assault",
        "severity": "HIGH",
        "location": (-18.0150, 31.0780),
        "area": "Chitungwiza",
        "language": "en"
    },
    
    # Vandalism and Property Damage
    {
        "raw_text": "Vandals broke windows at community school in Mabvuku. School property damaged.",
        "category": "vandalism",
        "severity": "MEDIUM",
        "location": (-17.9050, 31.0820),
        "area": "Mabvuku",
        "language": "en"
    },
    {
        "raw_text": "Graffiti and property damage reported in public park in Highlands. Unknown persons responsible.",
        "category": "vandalism",
        "severity": "LOW",
        "location": (-17.7700, 31.0400),
        "area": "Highlands",
        "language": "en"
    },
    {
        "raw_text": "Shop windows smashed during unrest in CBD. Multiple businesses affected.",
        "category": "vandalism",
        "severity": "HIGH",
        "location": (-17.8310, 31.0530),
        "area": "CBD",
        "language": "en"
    },
    {
        "raw_text": "Street lights being vandalized in Mbare. Copper wiring stolen from light poles.",
        "category": "theft",
        "severity": "MEDIUM",
        "location": (-17.8690, 31.0340),
        "area": "Mbare",
        "language": "en"
    },
    
    # Suspicious Activity
    {
        "raw_text": "Suspicious vehicle seen patrolling residential area in Mt Pleasant. No reports of crime but neighbors concerned.",
        "category": "suspicious_activity",
        "severity": "MEDIUM",
        "location": (-17.7650, 31.0600),
        "area": "Mt Pleasant",
        "language": "en"
    },
    {
        "raw_text": "Unknown person seen trying doors in townhouse complex in Borrowdale. Possible casing for burglary.",
        "category": "suspicious_activity",
        "severity": "MEDIUM",
        "location": (-17.7820, 31.0710),
        "area": "Borrowdale",
        "language": "en"
    },
    {
        "raw_text": "Group of people behaving suspiciously near bank ATM in CBD. Possible skimming device installation.",
        "category": "suspicious_activity",
        "severity": "MEDIUM",
        "location": (-17.8280, 31.0515),
        "area": "CBD",
        "language": "en"
    },
    {
        "raw_text": "Illegal street vendors causing obstruction and noise pollution in CBD. Authorities should regulate.",
        "category": "suspicious_activity",
        "severity": "LOW",
        "location": (-17.8300, 31.0520),
        "area": "CBD",
        "language": "en"
    },
    
    # Additional Realistic Incidents
    {
        "raw_text": "Passenger in commuter omnibus robbed of phone and cash. Threatened with knife during journey from CBD to Epworth.",
        "category": "robbery",
        "severity": "HIGH",
        "location": (-17.8350, 31.1000),
        "area": "Epworth",
        "language": "en"
    },
    {
        "raw_text": "Housebreaking in Rotten Row. Thieves gained entry through unsecured window and stole electronic goods.",
        "category": "theft",
        "severity": "HIGH",
        "location": (-17.8550, 31.1000),
        "area": "Rotten Row",
        "language": "en"
    },
    {
        "raw_text": "Farm produce theft reported in Hatfield. Agricultural equipment stolen from storage shed.",
        "category": "theft",
        "severity": "MEDIUM",
        "location": (-17.8700, 31.1200),
        "area": "hatfield",
        "language": "en"
    },
    {
        "raw_text": "Cybercrime case involving online banking fraud. Victim lost money through phishing scam.",
        "category": "fraud",
        "severity": "HIGH",
        "location": (-17.8280, 31.0520),
        "area": "CBD",
        "language": "en"
    },
    {
        "raw_text": "Illegal money changers operating in CBD. Converting illegal currency without authorization.",
        "category": "fraud",
        "severity": "MEDIUM",
        "location": (-17.8295, 31.0510),
        "area": "CBD",
        "language": "en"
    },
    {
        "raw_text": "Pickpocket targeting crowded bus terminus in Mbare. Multiple victims reported losing phones and wallets.",
        "category": "theft",
        "severity": "MEDIUM",
        "location": (-17.8640, 31.0320),
        "area": "Mbare",
        "language": "en"
    },
    {
        "raw_text": "Assault case at local bar in Kuwadzana. Bar fight escalated, one person seriously injured.",
        "category": "assault",
        "severity": "HIGH",
        "location": (-17.9300, 31.0300),
        "area": "Kuwadzana",
        "language": "en"
    },
    {
        "raw_text": "Sexual assault case reported in private college campus. Security increased.",
        "category": "assault",
        "severity": "HIGH",
        "location": (-17.8000, 31.0500),
        "area": "Mt Pleasant",
        "language": "en"
    },
    {
        "raw_text": "Land dispute turned violent in rural area on outskirts of Harare. One person injured.",
        "category": "assault",
        "severity": "HIGH",
        "location": (-17.7500, 31.1000),
        "area": "Rural Outskirts",
        "language": "en"
    },
    {
        "raw_text": "Illegal electricity connection discovered in Mufakose. Meter tampering detected.",
        "category": "theft",
        "severity": "MEDIUM",
        "location": (-17.9150, 31.0180),
        "area": "Mufakose",
        "language": "en"
    },
    {
        "raw_text": "Water theft by illegal connection in new residential area in Prospect. Municipal revenue loss.",
        "category": "theft",
        "severity": "LOW",
        "location": (-17.8600, 31.0600),
        "area": "Prospect",
        "language": "en"
    },
    {
        "raw_text": "Street children engaged in petty theft in CBD. Snatching food and small items from vendors.",
        "category": "theft",
        "severity": "LOW",
        "location": (-17.8310, 31.0500),
        "area": "CBD",
        "language": "en"
    },
    {
        "raw_text": "Human trafficking suspected in residential area. Young women being recruited with false job promises.",
        "category": "suspicious_activity",
        "severity": "HIGH",
        "location": (-17.8800, 31.0950),
        "area": "Dzivarasekwa",
        "language": "en"
    },
    {
        "raw_text": "Illegal gambling operation shut down in Highfields. Police confiscated equipment and cash.",
        "category": "suspicious_activity",
        "severity": "MEDIUM",
        "location": (-17.8880, 31.0120),
        "area": "Highfields",
        "language": "en"
    },
    {
        "raw_text": "Public transport bus involved in accident. Passenger reported theft of belongings during confusion.",
        "category": "theft",
        "severity": "MEDIUM",
        "location": (-17.8450, 31.0950),
        "area": "Ruwa",
        "language": "en"
    },
    {
        "raw_text": "Building materials theft from construction site in Newlands. Copper wiring and tools stolen.",
        "category": "theft",
        "severity": "MEDIUM",
        "location": (-17.7600, 31.0400),
        "area": "Newlands",
        "language": "en"
    },
    {
        "raw_text": "Night watchman attacked and tied up during robbery at warehouse in Workington. Thieves took valuable stock.",
        "category": "robbery",
        "severity": "HIGH",
        "location": (-17.8400, 31.1200),
        "area": "Workington",
        "language": "en"
    },
    {
        "raw_text": "Illegal land invasion reported in Houghton Park. People occupying undeveloped land without permission.",
        "category": "suspicious_activity",
        "severity": "MEDIUM",
        "location": (-17.7700, 31.0450),
        "area": "Houghton Park",
        "language": "en"
    },
    {
        "raw_text": "Stock theft from wholesale market in Mbare. Business lost significant inventory overnight.",
        "category": "theft",
        "severity": "HIGH",
        "location": (-17.8660, 31.0360),
        "area": "Mbare",
        "language": "en"
    },
    {
        "raw_text": "Fruit and vegetable theft from market stall in Harare CBD. Vendor lost entire day's produce.",
        "category": "theft",
        "severity": "MEDIUM",
        "location": (-17.8280, 31.0520),
        "area": "CBD",
        "language": "en"
    },
    {
        "raw_text": "Identity theft case where person's bank account was accessed and funds transferred to unknown account.",
        "category": "fraud",
        "severity": "HIGH",
        "location": (-17.8250, 31.0480),
        "area": "CBD",
        "language": "en"
    },
    {
        "raw_text": "Illegal mining activity reported in outskirts. Environmental damage and safety concerns.",
        "category": "suspicious_activity",
        "severity": "MEDIUM",
        "location": (-17.7500, 31.1500),
        "area": "Outskirts",
        "language": "en"
    },
    {
        "raw_text": "Counterfeit goods being sold in downtown area. Fake brands of clothing and electronics discovered.",
        "category": "fraud",
        "severity": "MEDIUM",
        "location": (-17.8300, 31.0520),
        "area": "CBD",
        "language": "en"
    },
    {
        "raw_text": "Taxi driver robbed by passengers who pretended to be customers. Dumped on roadside after robbery.",
        "category": "robbery",
        "severity": "HIGH",
        "location": (-17.8400, 31.0650),
        "area": "Msasa Park",
        "language": "en"
    },
    {
        "raw_text": "Home invasion robbery in Vainona. Armed men entered house, demanded cash and valuables at gunpoint.",
        "category": "robbery",
        "severity": "HIGH",
        "location": (-17.8900, 31.0800),
        "area": "Vainona",
        "language": "en"
    },
    {
        "raw_text": "Utility pole tampering for copper wire theft in Willowvale. Power outage affecting residents.",
        "category": "theft",
        "severity": "MEDIUM",
        "location": (-17.8800, 31.0600),
        "area": "Willowvale",
        "language": "en"
    },
    {
        "raw_text": "School bullying incident turned violent. Student assaulted by group of classmates.",
        "category": "assault",
        "severity": "MEDIUM",
        "location": (-17.8500, 31.1000),
        "area": "Greendale",
        "language": "en"
    },
    {
        "raw_text": "Road rage incident led to assault in Avondale. Drivers got into argument over traffic violation.",
        "category": "assault",
        "severity": "MEDIUM",
        "location": (-17.7580, 31.0520),
        "area": "Avondale",
        "language": "en"
    },
    {
        "raw_text": "Cyberstalking case reported in Harare North. Former partner harassing victim online and in person.",
        "category": "suspicious_activity",
        "severity": "MEDIUM",
        "location": (-17.7900, 31.0300),
        "area": "Harare North",
        "language": "en"
    },
    {
        "raw_text": "Rental scam reported in Belvedere. Fake landlord collected deposits from multiple tenants.",
        "category": "fraud",
        "severity": "HIGH",
        "location": (-17.8120, 31.0480),
        "area": "Belvedere",
        "language": "en"
    },
    {
        "raw_text": "Construction site theft in Waterfalls. Building materials and tools stolen overnight.",
        "category": "theft",
        "severity": "MEDIUM",
        "location": (-17.8250, 31.0900),
        "area": "Waterfalls",
        "language": "en"
    },
    {
        "raw_text": "Armed robbery at a service station in Chisipite. Thieves stole cash and cigarettes.",
        "category": "robbery",
        "severity": "HIGH",
        "location": (-17.8050, 31.0850),
        "area": "Chisipite",
        "language": "en"
    },
    {
        "raw_text": "Livestock theft in rural area. Goats and chickens stolen from smallholder's farm.",
        "category": "theft",
        "severity": "MEDIUM",
        "location": (-17.7400, 31.1200),
        "area": "Rural Area",
        "language": "en"
    },
    {
        "raw_text": "Group of youths involved in intimidation and extortion of small businesses in Arcadia.",
        "category": "extortion",
        "severity": "HIGH",
        "location": (-17.8700, 31.1100),
        "area": "Arcadia",
        "language": "en"
    },
]


def ensure_user(email, role, password):
    user = db.session.query(User).filter_by(email=email).first()
    if user:
        return user

    user = User(email=email, role=role)
    user.set_password(password)
    db.session.add(user)
    db.session.flush()
    return user


def make_summary(category, area):
    category_text = category.replace("_", " ")
    return f"{category_text} reported in {area}, Harare."


def main():
    random.seed(20260816)  # Seed for reproducibility
    app = create_app("development")

    with app.app_context():
        # Ensure test users exist
        officer = ensure_user("officer@crimewatch.zw", "officer", "Officer1234!")
        ensure_user("admin@crimewatch.zw", "admin", "Admin1234!")
        ensure_user("officer@harare.gov.zw", "officer", "password123")
        ensure_user("community@harare.gov.zw", "community", "password123")

        # Clear existing realistic incidents
        db.session.query(Incident).filter(
            Incident.raw_text.like("Realistic Harare seed:%")
        ).delete(synchronize_session=False)

        now = datetime.now(timezone.utc)
        total_created = 0

        for incident_data in REALISTIC_INCIDENTS:
            # Add some temporal randomness (incidents spread over past 90 days)
            days_ago = random.randint(0, 90)
            hours_ago = random.randint(0, 23)
            
            # Add triage confidence (simulating NLP processing)
            triage_confidence = round(random.uniform(0.75, 0.98), 2)
            
            incident = Incident(
                raw_text=f"Realistic Harare seed: {incident_data['raw_text']}",
                language_detected=incident_data['language'],
                category=incident_data['category'],
                severity=incident_data['severity'],
                triage_confidence=triage_confidence,
                triage_summary=make_summary(incident_data['category'], incident_data['area']),
                raw_gemini_response=None,  # Not generated in seed data
                status="TRIAGED",
                lat=incident_data['location'][0],
                lng=incident_data['location'][1],
                location_description=f"{incident_data['area']}, Harare",
                reported_by_id=officer.id,
                created_at=now - timedelta(days=days_ago, hours=hours_ago),
                occurred_at=now - timedelta(days=days_ago, hours=hours_ago + random.randint(0, 12)),  # Occurred a few hours before report
            )
            db.session.add(incident)
            total_created += 1

        db.session.commit()
        print(f"Seeded {total_created} realistic crime incidents across Harare")
        print(f"  - Covered {len(set(i['area'] for i in REALISTIC_INCIDENTS))} different areas")
        print(f"  - Incident types: {len(set(i['category'] for i in REALISTIC_INCIDENTS))} different categories")
        print(f"  - Languages: {len(set(i['language'] for i in REALISTIC_INCIDENTS))} different languages")
        print(f"  - Severity distribution: {sum(1 for i in REALISTIC_INCIDENTS if i['severity'] == 'HIGH')} HIGH, {sum(1 for i in REALISTIC_INCIDENTS if i['severity'] == 'MEDIUM')} MEDIUM, {sum(1 for i in REALISTIC_INCIDENTS if i['severity'] == 'LOW')} LOW")


if __name__ == "__main__":
    main()
