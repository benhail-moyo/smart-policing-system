import { db } from "@/db";
import { users, incidents } from "@/db/schema";
import { hashPassword, generateToken } from "@/lib/auth";
import { triage, CRIME_TYPES } from "@/lib/crime";

export const dynamic = "force-dynamic";

// Extended Harare suburb clusters with realistic coordinates
const CLUSTERS: { name: string; lat: number; lng: number; n: number }[] = [
  { name: "CBD", lat: -17.8292, lng: 31.0522, n: 28 },
  { name: "Mbare", lat: -17.8564, lng: 31.0301, n: 24 },
  { name: "Avenues", lat: -17.8189, lng: 31.0433, n: 18 },
  { name: "Highfield", lat: -17.8721, lng: 31.0022, n: 20 },
  { name: "Avondale", lat: -17.8016, lng: 31.0389, n: 14 },
  { name: "Waterfalls", lat: -17.8901, lng: 31.0555, n: 16 },
  { name: "Borrowdale", lat: -17.7501, lng: 31.0889, n: 12 },
  { name: "Budiriro", lat: -17.8626, lng: 31.0097, n: 14 },
  { name: "Glen Norah", lat: -17.8473, lng: 30.9961, n: 12 },
  { name: "Kuwadzana", lat: -17.7968, lng: 30.9822, n: 10 },
  { name: "Kuwadzana Ext", lat: -17.7922, lng: 30.9766, n: 8 },
  { name: "Dzivarasekwa", lat: -17.8012, lng: 30.9689, n: 10 },
  { name: "Hatfield", lat: -17.8812, lng: 31.0944, n: 9 },
  { name: "Mount Pleasant", lat: -17.7685, lng: 31.0449, n: 9 },
  { name: "Marlborough", lat: -17.7523, lng: 31.0099, n: 7 },
  { name: "Greendale", lat: -17.8101, lng: 31.1193, n: 8 },
  { name: "Southerton", lat: -17.8512, lng: 31.0211, n: 11 },
  { name: "Arcadia", lat: -17.8391, lng: 31.0677, n: 9 },
  { name: "Eastlea", lat: -17.8133, lng: 31.0722, n: 8 },
  { name: "Belvedere", lat: -17.8289, lng: 31.0199, n: 8 },
];

const REPORTERS = [
  "Tendai Moyo", "Rudo Sibanda", "Farai Chitepo", "Nyasha Dube",
  "Tinashe Makoni", "Chipo Zulu", "Blessing Ncube", "Kuda Mutasa",
  "Simba Chigwada", "Mutsa Gumbo", "Tafara Hove", "Ruvimbo Dziva",
];

const INCIDENT_DESCRIPTIONS: Record<string, string[]> = {
  "Armed Robbery": [
    "Armed suspects demanded cash and valuables at gunpoint.",
    "Group of armed men stormed the premises, took electronics and cash.",
    "Victim was held at gunpoint near the bus stop; phone and wallet stolen.",
    "Armed robbers targeted a delivery vehicle, fled with goods.",
  ],
  "Assault": [
    "Victim sustained injuries after being attacked by unknown assailants.",
    "Physical altercation escalated; victim taken to hospital.",
    "Domestic assault reported by neighbours who heard screaming.",
    "Bar fight resulted in serious injuries to two individuals.",
  ],
  "Burglary": [
    "Residence broken into while occupants were away; valuables missing.",
    "Office premises burgled overnight; computers and safe compromised.",
    "Break-in through rear window; jewellery and electronics stolen.",
    "Storage unit forced open; construction equipment taken.",
  ],
  "Carjacking": [
    "Vehicle hijacked at traffic lights; driver forced out at knifepoint.",
    "Parked car stolen from shopping centre car park.",
    "Armed carjacking on a residential driveway during morning hours.",
    "Ride-share driver's vehicle taken by passengers posing as clients.",
  ],
  "Theft": [
    "Pickpocketing reported in a crowded market area.",
    "Mobile phone snatched from pedestrian's hand on the street.",
    "Bag stolen from restaurant table while victim was distracted.",
    "Bicycle taken from outside a shop; chain was cut.",
  ],
  "Vandalism": [
    "Public property defaced with graffiti and minor fire damage.",
    "Several vehicles had windows smashed along the street overnight.",
    "Park benches and signage destroyed near the community hall.",
    "School perimeter wall damaged; stones thrown at classroom windows.",
  ],
  "Drug Offense": [
    "Suspected drug dealing activity in abandoned building.",
    "Individual arrested with substantial quantity of illegal substances.",
    "Drug paraphernalia found near the sports ground.",
    "Neighbourhood tip-off about a house being used for drug distribution.",
  ],
  "Fraud": [
    "Elderly resident targeted by phone scam; bank details compromised.",
    "Fake investment scheme discovered operating in the area.",
    "Identity theft case; fraudulent loan taken in victim's name.",
    "Counterfeit currency being circulated at informal market stalls.",
  ],
  "Public Disturbance": [
    "Loud party escalated into a public disturbance; police called.",
    "Street vendor dispute turned violent, blocking traffic.",
    "Protest gathering near government offices; minor injuries.",
    "Drunk and disorderly behaviour outside a nightclub.",
  ],
  "Kidnapping": [
    "Child approached by strangers near school; parent intervened.",
    "Businessman abducted briefly, released after family paid ransom.",
    "Attempted kidnapping of a teenager on the way home; escaped.",
    "Suspicious vehicle following students reported to authorities.",
  ],
};

function rand(seed: number) {
  const x = Math.sin(seed) * 10000;
  return x - Math.floor(x);
}

export async function POST() {
  // Seed demo users (idempotent)
  const existingUsers = await db.select().from(users).limit(1);
  if (!existingUsers[0]) {
    await db.insert(users).values([
      {
        name: "Officer Chikwava",
        email: "officer@harare.gov.zw",
        password: hashPassword("password123"),
        role: "officer",
        token: generateToken(),
      },
      {
        name: "Command Admin",
        email: "admin@harare.gov.zw",
        password: hashPassword("password123"),
        role: "admin",
        token: generateToken(),
      },
      {
        name: "Tendai Moyo",
        email: "community@harare.gov.zw",
        password: hashPassword("password123"),
        role: "community",
        token: generateToken(),
      },
    ]);
  }

  const existingIncidents = await db.select().from(incidents).limit(1);
  if (!existingIncidents[0]) {
    const rows: (typeof incidents.$inferInsert)[] = [];
    let seed = 1;

    for (const c of CLUSTERS) {
      for (let i = 0; i < c.n; i++) {
        const lat = c.lat + (rand(seed++) - 0.5) * 0.015;
        const lng = c.lng + (rand(seed++) - 0.5) * 0.015;
        const type =
          CRIME_TYPES[Math.floor(rand(seed++) * CRIME_TYPES.length)];
        const severity = 1 + Math.floor(rand(seed++) * 5);
        const t = triage(type, severity);
        // spread over 45 days
        const ageDays = Math.floor(rand(seed++) * 45);
        // random hour 0-23
        const hour = Math.floor(rand(seed++) * 24);

        // status spread
        const s = rand(seed++);
        const status =
          s < 0.45 ? "reported" : s < 0.70 ? "dispatched" : "resolved";

        // pick a description
        const descs = INCIDENT_DESCRIPTIONS[type] ?? [
          `${type} incident in ${c.name}.`,
        ];
        const description = descs[Math.floor(rand(seed++) * descs.length)];

        const reporter = REPORTERS[Math.floor(rand(seed++) * REPORTERS.length)];

        const d = new Date(Date.now() - ageDays * 86400000);
        d.setHours(hour, Math.floor(rand(seed++) * 60), 0, 0);

        rows.push({
          type,
          description,
          lat,
          lng,
          severity,
          priority: t.priority,
          triageScore: t.score,
          suburb: c.name,
          reportedBy: reporter,
          status,
          createdAt: d,
        });
      }
    }

    // batch insert
    for (let i = 0; i < rows.length; i += 80) {
      await db.insert(incidents).values(rows.slice(i, i + 80));
    }
  }

  const totalUsers = await db.select().from(users);
  const totalIncidents = await db.select().from(incidents);

  return Response.json({
    seeded: true,
    users: totalUsers.length,
    incidents: totalIncidents.length,
    demoAccounts: [
      { role: "officer", email: "officer@harare.gov.zw", password: "password123" },
      { role: "admin", email: "admin@harare.gov.zw", password: "password123" },
      {
        role: "community",
        email: "community@harare.gov.zw",
        password: "password123",
      },
    ],
  });
}
