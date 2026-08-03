import {
  pgTable,
  serial,
  text,
  varchar,
  doublePrecision,
  integer,
  timestamp,
  jsonb,
} from "drizzle-orm/pg-core";

export const users = pgTable("users", {
  id: serial("id").primaryKey(),
  name: varchar("name", { length: 120 }).notNull(),
  email: varchar("email", { length: 160 }).notNull().unique(),
  password: varchar("password", { length: 200 }).notNull(),
  // "community" | "officer" | "admin"
  role: varchar("role", { length: 20 }).notNull().default("community"),
  token: varchar("token", { length: 120 }),
  createdAt: timestamp("created_at").notNull().defaultNow(),
});

export const incidents = pgTable("incidents", {
  id: serial("id").primaryKey(),
  // crime category
  type: varchar("type", { length: 60 }).notNull(),
  description: text("description").notNull(),
  lat: doublePrecision("lat").notNull(),
  lng: doublePrecision("lng").notNull(),
  // reporter provided severity 1..5
  severity: integer("severity").notNull().default(3),
  // "reported" | "dispatched" | "resolved"
  status: varchar("status", { length: 20 }).notNull().default("reported"),
  // computed triage priority: "critical" | "high" | "medium" | "low"
  priority: varchar("priority", { length: 20 }).notNull().default("medium"),
  triageScore: integer("triage_score").notNull().default(0),
  suburb: varchar("suburb", { length: 80 }),
  reportedBy: varchar("reported_by", { length: 120 }),
  createdAt: timestamp("created_at").notNull().defaultNow(),
});

export const hotspots = pgTable("hotspots", {
  id: serial("id").primaryKey(),
  lat: doublePrecision("lat").notNull(),
  lng: doublePrecision("lng").notNull(),
  // number of incidents contributing to the cluster
  count: integer("count").notNull().default(0),
  // weighted score based on severity + priority
  weight: doublePrecision("weight").notNull().default(0),
  // radius in meters
  radius: integer("radius").notNull().default(400),
  // "high" | "medium" | "low"
  level: varchar("level", { length: 20 }).notNull().default("low"),
  topTypes: jsonb("top_types").$type<string[]>().default([]),
  createdAt: timestamp("created_at").notNull().defaultNow(),
});
