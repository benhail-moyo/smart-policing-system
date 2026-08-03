module.exports = [
"[externals]/next/dist/compiled/next-server/app-route-turbo.runtime.dev.js [external] (next/dist/compiled/next-server/app-route-turbo.runtime.dev.js, cjs)", ((__turbopack_context__, module, exports) => {

const mod = __turbopack_context__.x("next/dist/compiled/next-server/app-route-turbo.runtime.dev.js", () => require("next/dist/compiled/next-server/app-route-turbo.runtime.dev.js"));

module.exports = mod;
}),
"[externals]/next/dist/compiled/@opentelemetry/api [external] (next/dist/compiled/@opentelemetry/api, cjs)", ((__turbopack_context__, module, exports) => {

const mod = __turbopack_context__.x("next/dist/compiled/@opentelemetry/api", () => require("next/dist/compiled/@opentelemetry/api"));

module.exports = mod;
}),
"[externals]/next/dist/compiled/next-server/app-page-turbo.runtime.dev.js [external] (next/dist/compiled/next-server/app-page-turbo.runtime.dev.js, cjs)", ((__turbopack_context__, module, exports) => {

const mod = __turbopack_context__.x("next/dist/compiled/next-server/app-page-turbo.runtime.dev.js", () => require("next/dist/compiled/next-server/app-page-turbo.runtime.dev.js"));

module.exports = mod;
}),
"[externals]/next/dist/server/app-render/work-unit-async-storage.external.js [external] (next/dist/server/app-render/work-unit-async-storage.external.js, cjs)", ((__turbopack_context__, module, exports) => {

const mod = __turbopack_context__.x("next/dist/server/app-render/work-unit-async-storage.external.js", () => require("next/dist/server/app-render/work-unit-async-storage.external.js"));

module.exports = mod;
}),
"[externals]/next/dist/server/app-render/work-async-storage.external.js [external] (next/dist/server/app-render/work-async-storage.external.js, cjs)", ((__turbopack_context__, module, exports) => {

const mod = __turbopack_context__.x("next/dist/server/app-render/work-async-storage.external.js", () => require("next/dist/server/app-render/work-async-storage.external.js"));

module.exports = mod;
}),
"[externals]/next/dist/shared/lib/no-fallback-error.external.js [external] (next/dist/shared/lib/no-fallback-error.external.js, cjs)", ((__turbopack_context__, module, exports) => {

const mod = __turbopack_context__.x("next/dist/shared/lib/no-fallback-error.external.js", () => require("next/dist/shared/lib/no-fallback-error.external.js"));

module.exports = mod;
}),
"[project]/crime-watch-ui/extracted/src/db/index.ts [app-route] (ecmascript)", ((__turbopack_context__) => {
"use strict";

return __turbopack_context__.a(async (__turbopack_handle_async_dependencies__, __turbopack_async_result__) => { try {

__turbopack_context__.s([
    "db",
    ()=>db,
    "pool",
    ()=>pool
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$crime$2d$watch$2d$ui$2f$extracted$2f$node_modules$2f$drizzle$2d$orm$2f$node$2d$postgres$2f$driver$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/crime-watch-ui/extracted/node_modules/drizzle-orm/node-postgres/driver.js [app-route] (ecmascript)");
var __TURBOPACK__imported__module__$5b$externals$5d2f$pg__$5b$external$5d$__$28$pg$2c$__esm_import$2c$__$5b$project$5d2f$crime$2d$watch$2d$ui$2f$extracted$2f$node_modules$2f$pg$29$__ = __turbopack_context__.i("[externals]/pg [external] (pg, esm_import, [project]/crime-watch-ui/extracted/node_modules/pg)");
var __turbopack_async_dependencies__ = __turbopack_handle_async_dependencies__([
    __TURBOPACK__imported__module__$5b$project$5d2f$crime$2d$watch$2d$ui$2f$extracted$2f$node_modules$2f$drizzle$2d$orm$2f$node$2d$postgres$2f$driver$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__,
    __TURBOPACK__imported__module__$5b$externals$5d2f$pg__$5b$external$5d$__$28$pg$2c$__esm_import$2c$__$5b$project$5d2f$crime$2d$watch$2d$ui$2f$extracted$2f$node_modules$2f$pg$29$__
]);
[__TURBOPACK__imported__module__$5b$project$5d2f$crime$2d$watch$2d$ui$2f$extracted$2f$node_modules$2f$drizzle$2d$orm$2f$node$2d$postgres$2f$driver$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__, __TURBOPACK__imported__module__$5b$externals$5d2f$pg__$5b$external$5d$__$28$pg$2c$__esm_import$2c$__$5b$project$5d2f$crime$2d$watch$2d$ui$2f$extracted$2f$node_modules$2f$pg$29$__] = __turbopack_async_dependencies__.then ? (await __turbopack_async_dependencies__)() : __turbopack_async_dependencies__;
;
;
const databaseUrl = process.env.DATABASE_URL;
if (!databaseUrl) {
    throw new Error("DATABASE_URL is required");
}
const globalForDb = globalThis;
const pool = globalForDb.__arenaNextJsPostgresqlPool ?? new __TURBOPACK__imported__module__$5b$externals$5d2f$pg__$5b$external$5d$__$28$pg$2c$__esm_import$2c$__$5b$project$5d2f$crime$2d$watch$2d$ui$2f$extracted$2f$node_modules$2f$pg$29$__["Pool"]({
    connectionString: databaseUrl
});
if ("TURBOPACK compile-time truthy", 1) {
    globalForDb.__arenaNextJsPostgresqlPool = pool;
}
const db = (0, __TURBOPACK__imported__module__$5b$project$5d2f$crime$2d$watch$2d$ui$2f$extracted$2f$node_modules$2f$drizzle$2d$orm$2f$node$2d$postgres$2f$driver$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__["drizzle"])(pool);
__turbopack_async_result__();
} catch(e) { __turbopack_async_result__(e); } }, false);}),
"[project]/crime-watch-ui/extracted/src/db/schema.ts [app-route] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "hotspots",
    ()=>hotspots,
    "incidents",
    ()=>incidents,
    "users",
    ()=>users
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$crime$2d$watch$2d$ui$2f$extracted$2f$node_modules$2f$drizzle$2d$orm$2f$pg$2d$core$2f$table$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/crime-watch-ui/extracted/node_modules/drizzle-orm/pg-core/table.js [app-route] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$crime$2d$watch$2d$ui$2f$extracted$2f$node_modules$2f$drizzle$2d$orm$2f$pg$2d$core$2f$columns$2f$serial$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/crime-watch-ui/extracted/node_modules/drizzle-orm/pg-core/columns/serial.js [app-route] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$crime$2d$watch$2d$ui$2f$extracted$2f$node_modules$2f$drizzle$2d$orm$2f$pg$2d$core$2f$columns$2f$text$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/crime-watch-ui/extracted/node_modules/drizzle-orm/pg-core/columns/text.js [app-route] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$crime$2d$watch$2d$ui$2f$extracted$2f$node_modules$2f$drizzle$2d$orm$2f$pg$2d$core$2f$columns$2f$varchar$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/crime-watch-ui/extracted/node_modules/drizzle-orm/pg-core/columns/varchar.js [app-route] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$crime$2d$watch$2d$ui$2f$extracted$2f$node_modules$2f$drizzle$2d$orm$2f$pg$2d$core$2f$columns$2f$double$2d$precision$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/crime-watch-ui/extracted/node_modules/drizzle-orm/pg-core/columns/double-precision.js [app-route] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$crime$2d$watch$2d$ui$2f$extracted$2f$node_modules$2f$drizzle$2d$orm$2f$pg$2d$core$2f$columns$2f$integer$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/crime-watch-ui/extracted/node_modules/drizzle-orm/pg-core/columns/integer.js [app-route] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$crime$2d$watch$2d$ui$2f$extracted$2f$node_modules$2f$drizzle$2d$orm$2f$pg$2d$core$2f$columns$2f$timestamp$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/crime-watch-ui/extracted/node_modules/drizzle-orm/pg-core/columns/timestamp.js [app-route] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$crime$2d$watch$2d$ui$2f$extracted$2f$node_modules$2f$drizzle$2d$orm$2f$pg$2d$core$2f$columns$2f$jsonb$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/crime-watch-ui/extracted/node_modules/drizzle-orm/pg-core/columns/jsonb.js [app-route] (ecmascript)");
;
const users = (0, __TURBOPACK__imported__module__$5b$project$5d2f$crime$2d$watch$2d$ui$2f$extracted$2f$node_modules$2f$drizzle$2d$orm$2f$pg$2d$core$2f$table$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__["pgTable"])("users", {
    id: (0, __TURBOPACK__imported__module__$5b$project$5d2f$crime$2d$watch$2d$ui$2f$extracted$2f$node_modules$2f$drizzle$2d$orm$2f$pg$2d$core$2f$columns$2f$serial$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__["serial"])("id").primaryKey(),
    name: (0, __TURBOPACK__imported__module__$5b$project$5d2f$crime$2d$watch$2d$ui$2f$extracted$2f$node_modules$2f$drizzle$2d$orm$2f$pg$2d$core$2f$columns$2f$varchar$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__["varchar"])("name", {
        length: 120
    }).notNull(),
    email: (0, __TURBOPACK__imported__module__$5b$project$5d2f$crime$2d$watch$2d$ui$2f$extracted$2f$node_modules$2f$drizzle$2d$orm$2f$pg$2d$core$2f$columns$2f$varchar$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__["varchar"])("email", {
        length: 160
    }).notNull().unique(),
    password: (0, __TURBOPACK__imported__module__$5b$project$5d2f$crime$2d$watch$2d$ui$2f$extracted$2f$node_modules$2f$drizzle$2d$orm$2f$pg$2d$core$2f$columns$2f$varchar$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__["varchar"])("password", {
        length: 200
    }).notNull(),
    // "community" | "officer" | "admin"
    role: (0, __TURBOPACK__imported__module__$5b$project$5d2f$crime$2d$watch$2d$ui$2f$extracted$2f$node_modules$2f$drizzle$2d$orm$2f$pg$2d$core$2f$columns$2f$varchar$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__["varchar"])("role", {
        length: 20
    }).notNull().default("community"),
    token: (0, __TURBOPACK__imported__module__$5b$project$5d2f$crime$2d$watch$2d$ui$2f$extracted$2f$node_modules$2f$drizzle$2d$orm$2f$pg$2d$core$2f$columns$2f$varchar$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__["varchar"])("token", {
        length: 120
    }),
    createdAt: (0, __TURBOPACK__imported__module__$5b$project$5d2f$crime$2d$watch$2d$ui$2f$extracted$2f$node_modules$2f$drizzle$2d$orm$2f$pg$2d$core$2f$columns$2f$timestamp$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__["timestamp"])("created_at").notNull().defaultNow()
});
const incidents = (0, __TURBOPACK__imported__module__$5b$project$5d2f$crime$2d$watch$2d$ui$2f$extracted$2f$node_modules$2f$drizzle$2d$orm$2f$pg$2d$core$2f$table$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__["pgTable"])("incidents", {
    id: (0, __TURBOPACK__imported__module__$5b$project$5d2f$crime$2d$watch$2d$ui$2f$extracted$2f$node_modules$2f$drizzle$2d$orm$2f$pg$2d$core$2f$columns$2f$serial$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__["serial"])("id").primaryKey(),
    // crime category
    type: (0, __TURBOPACK__imported__module__$5b$project$5d2f$crime$2d$watch$2d$ui$2f$extracted$2f$node_modules$2f$drizzle$2d$orm$2f$pg$2d$core$2f$columns$2f$varchar$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__["varchar"])("type", {
        length: 60
    }).notNull(),
    description: (0, __TURBOPACK__imported__module__$5b$project$5d2f$crime$2d$watch$2d$ui$2f$extracted$2f$node_modules$2f$drizzle$2d$orm$2f$pg$2d$core$2f$columns$2f$text$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__["text"])("description").notNull(),
    lat: (0, __TURBOPACK__imported__module__$5b$project$5d2f$crime$2d$watch$2d$ui$2f$extracted$2f$node_modules$2f$drizzle$2d$orm$2f$pg$2d$core$2f$columns$2f$double$2d$precision$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__["doublePrecision"])("lat").notNull(),
    lng: (0, __TURBOPACK__imported__module__$5b$project$5d2f$crime$2d$watch$2d$ui$2f$extracted$2f$node_modules$2f$drizzle$2d$orm$2f$pg$2d$core$2f$columns$2f$double$2d$precision$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__["doublePrecision"])("lng").notNull(),
    // reporter provided severity 1..5
    severity: (0, __TURBOPACK__imported__module__$5b$project$5d2f$crime$2d$watch$2d$ui$2f$extracted$2f$node_modules$2f$drizzle$2d$orm$2f$pg$2d$core$2f$columns$2f$integer$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__["integer"])("severity").notNull().default(3),
    // "reported" | "dispatched" | "resolved"
    status: (0, __TURBOPACK__imported__module__$5b$project$5d2f$crime$2d$watch$2d$ui$2f$extracted$2f$node_modules$2f$drizzle$2d$orm$2f$pg$2d$core$2f$columns$2f$varchar$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__["varchar"])("status", {
        length: 20
    }).notNull().default("reported"),
    // computed triage priority: "critical" | "high" | "medium" | "low"
    priority: (0, __TURBOPACK__imported__module__$5b$project$5d2f$crime$2d$watch$2d$ui$2f$extracted$2f$node_modules$2f$drizzle$2d$orm$2f$pg$2d$core$2f$columns$2f$varchar$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__["varchar"])("priority", {
        length: 20
    }).notNull().default("medium"),
    triageScore: (0, __TURBOPACK__imported__module__$5b$project$5d2f$crime$2d$watch$2d$ui$2f$extracted$2f$node_modules$2f$drizzle$2d$orm$2f$pg$2d$core$2f$columns$2f$integer$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__["integer"])("triage_score").notNull().default(0),
    suburb: (0, __TURBOPACK__imported__module__$5b$project$5d2f$crime$2d$watch$2d$ui$2f$extracted$2f$node_modules$2f$drizzle$2d$orm$2f$pg$2d$core$2f$columns$2f$varchar$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__["varchar"])("suburb", {
        length: 80
    }),
    reportedBy: (0, __TURBOPACK__imported__module__$5b$project$5d2f$crime$2d$watch$2d$ui$2f$extracted$2f$node_modules$2f$drizzle$2d$orm$2f$pg$2d$core$2f$columns$2f$varchar$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__["varchar"])("reported_by", {
        length: 120
    }),
    createdAt: (0, __TURBOPACK__imported__module__$5b$project$5d2f$crime$2d$watch$2d$ui$2f$extracted$2f$node_modules$2f$drizzle$2d$orm$2f$pg$2d$core$2f$columns$2f$timestamp$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__["timestamp"])("created_at").notNull().defaultNow()
});
const hotspots = (0, __TURBOPACK__imported__module__$5b$project$5d2f$crime$2d$watch$2d$ui$2f$extracted$2f$node_modules$2f$drizzle$2d$orm$2f$pg$2d$core$2f$table$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__["pgTable"])("hotspots", {
    id: (0, __TURBOPACK__imported__module__$5b$project$5d2f$crime$2d$watch$2d$ui$2f$extracted$2f$node_modules$2f$drizzle$2d$orm$2f$pg$2d$core$2f$columns$2f$serial$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__["serial"])("id").primaryKey(),
    lat: (0, __TURBOPACK__imported__module__$5b$project$5d2f$crime$2d$watch$2d$ui$2f$extracted$2f$node_modules$2f$drizzle$2d$orm$2f$pg$2d$core$2f$columns$2f$double$2d$precision$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__["doublePrecision"])("lat").notNull(),
    lng: (0, __TURBOPACK__imported__module__$5b$project$5d2f$crime$2d$watch$2d$ui$2f$extracted$2f$node_modules$2f$drizzle$2d$orm$2f$pg$2d$core$2f$columns$2f$double$2d$precision$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__["doublePrecision"])("lng").notNull(),
    // number of incidents contributing to the cluster
    count: (0, __TURBOPACK__imported__module__$5b$project$5d2f$crime$2d$watch$2d$ui$2f$extracted$2f$node_modules$2f$drizzle$2d$orm$2f$pg$2d$core$2f$columns$2f$integer$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__["integer"])("count").notNull().default(0),
    // weighted score based on severity + priority
    weight: (0, __TURBOPACK__imported__module__$5b$project$5d2f$crime$2d$watch$2d$ui$2f$extracted$2f$node_modules$2f$drizzle$2d$orm$2f$pg$2d$core$2f$columns$2f$double$2d$precision$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__["doublePrecision"])("weight").notNull().default(0),
    // radius in meters
    radius: (0, __TURBOPACK__imported__module__$5b$project$5d2f$crime$2d$watch$2d$ui$2f$extracted$2f$node_modules$2f$drizzle$2d$orm$2f$pg$2d$core$2f$columns$2f$integer$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__["integer"])("radius").notNull().default(400),
    // "high" | "medium" | "low"
    level: (0, __TURBOPACK__imported__module__$5b$project$5d2f$crime$2d$watch$2d$ui$2f$extracted$2f$node_modules$2f$drizzle$2d$orm$2f$pg$2d$core$2f$columns$2f$varchar$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__["varchar"])("level", {
        length: 20
    }).notNull().default("low"),
    topTypes: (0, __TURBOPACK__imported__module__$5b$project$5d2f$crime$2d$watch$2d$ui$2f$extracted$2f$node_modules$2f$drizzle$2d$orm$2f$pg$2d$core$2f$columns$2f$jsonb$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__["jsonb"])("top_types").$type().default([]),
    createdAt: (0, __TURBOPACK__imported__module__$5b$project$5d2f$crime$2d$watch$2d$ui$2f$extracted$2f$node_modules$2f$drizzle$2d$orm$2f$pg$2d$core$2f$columns$2f$timestamp$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__["timestamp"])("created_at").notNull().defaultNow()
});
}),
"[externals]/crypto [external] (crypto, cjs)", ((__turbopack_context__, module, exports) => {

const mod = __turbopack_context__.x("crypto", () => require("crypto"));

module.exports = mod;
}),
"[project]/crime-watch-ui/extracted/src/lib/auth.ts [app-route] (ecmascript)", ((__turbopack_context__) => {
"use strict";

return __turbopack_context__.a(async (__turbopack_handle_async_dependencies__, __turbopack_async_result__) => { try {

__turbopack_context__.s([
    "generateToken",
    ()=>generateToken,
    "getUserFromToken",
    ()=>getUserFromToken,
    "hashPassword",
    ()=>hashPassword,
    "requireUser",
    ()=>requireUser,
    "verifyPassword",
    ()=>verifyPassword
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$crime$2d$watch$2d$ui$2f$extracted$2f$src$2f$db$2f$index$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/crime-watch-ui/extracted/src/db/index.ts [app-route] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$crime$2d$watch$2d$ui$2f$extracted$2f$src$2f$db$2f$schema$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/crime-watch-ui/extracted/src/db/schema.ts [app-route] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$crime$2d$watch$2d$ui$2f$extracted$2f$node_modules$2f$drizzle$2d$orm$2f$sql$2f$expressions$2f$conditions$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/crime-watch-ui/extracted/node_modules/drizzle-orm/sql/expressions/conditions.js [app-route] (ecmascript)");
var __TURBOPACK__imported__module__$5b$externals$5d2f$crypto__$5b$external$5d$__$28$crypto$2c$__cjs$29$__ = __turbopack_context__.i("[externals]/crypto [external] (crypto, cjs)");
var __turbopack_async_dependencies__ = __turbopack_handle_async_dependencies__([
    __TURBOPACK__imported__module__$5b$project$5d2f$crime$2d$watch$2d$ui$2f$extracted$2f$src$2f$db$2f$index$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__
]);
[__TURBOPACK__imported__module__$5b$project$5d2f$crime$2d$watch$2d$ui$2f$extracted$2f$src$2f$db$2f$index$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__] = __turbopack_async_dependencies__.then ? (await __turbopack_async_dependencies__)() : __turbopack_async_dependencies__;
;
;
;
;
function hashPassword(password) {
    const salt = (0, __TURBOPACK__imported__module__$5b$externals$5d2f$crypto__$5b$external$5d$__$28$crypto$2c$__cjs$29$__["randomBytes"])(16).toString("hex");
    const hash = (0, __TURBOPACK__imported__module__$5b$externals$5d2f$crypto__$5b$external$5d$__$28$crypto$2c$__cjs$29$__["scryptSync"])(password, salt, 64).toString("hex");
    return `${salt}:${hash}`;
}
function verifyPassword(password, stored) {
    const [salt, hash] = stored.split(":");
    if (!salt || !hash) return false;
    const hashBuffer = Buffer.from(hash, "hex");
    const test = (0, __TURBOPACK__imported__module__$5b$externals$5d2f$crypto__$5b$external$5d$__$28$crypto$2c$__cjs$29$__["scryptSync"])(password, salt, 64);
    if (hashBuffer.length !== test.length) return false;
    return (0, __TURBOPACK__imported__module__$5b$externals$5d2f$crypto__$5b$external$5d$__$28$crypto$2c$__cjs$29$__["timingSafeEqual"])(hashBuffer, test);
}
function generateToken() {
    return (0, __TURBOPACK__imported__module__$5b$externals$5d2f$crypto__$5b$external$5d$__$28$crypto$2c$__cjs$29$__["randomBytes"])(32).toString("hex");
}
async function getUserFromToken(token) {
    if (!token) return null;
    const rows = await __TURBOPACK__imported__module__$5b$project$5d2f$crime$2d$watch$2d$ui$2f$extracted$2f$src$2f$db$2f$index$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__["db"].select().from(__TURBOPACK__imported__module__$5b$project$5d2f$crime$2d$watch$2d$ui$2f$extracted$2f$src$2f$db$2f$schema$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__["users"]).where((0, __TURBOPACK__imported__module__$5b$project$5d2f$crime$2d$watch$2d$ui$2f$extracted$2f$node_modules$2f$drizzle$2d$orm$2f$sql$2f$expressions$2f$conditions$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__["eq"])(__TURBOPACK__imported__module__$5b$project$5d2f$crime$2d$watch$2d$ui$2f$extracted$2f$src$2f$db$2f$schema$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__["users"].token, token)).limit(1);
    const u = rows[0];
    if (!u) return null;
    return {
        id: u.id,
        name: u.name,
        email: u.email,
        role: u.role
    };
}
async function requireUser(request) {
    const header = request.headers.get("authorization");
    const token = header?.startsWith("Bearer ") ? header.slice(7) : header ?? null;
    return getUserFromToken(token);
}
__turbopack_async_result__();
} catch(e) { __turbopack_async_result__(e); } }, false);}),
"[project]/crime-watch-ui/extracted/src/lib/crime.ts [app-route] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "CRIME_TYPES",
    ()=>CRIME_TYPES,
    "HARARE_CENTER",
    ()=>HARARE_CENTER,
    "PATROL_ROUTES",
    ()=>PATROL_ROUTES,
    "PRIORITY_ORDER",
    ()=>PRIORITY_ORDER,
    "analyzeHotspots",
    ()=>analyzeHotspots,
    "haversineKm",
    ()=>haversineKm,
    "routeLengthKm",
    ()=>routeLengthKm,
    "triage",
    ()=>triage
]);
const HARARE_CENTER = {
    lat: -17.8292,
    lng: 31.0522
};
const CRIME_TYPES = [
    "Armed Robbery",
    "Assault",
    "Burglary",
    "Carjacking",
    "Theft",
    "Vandalism",
    "Drug Offense",
    "Fraud",
    "Public Disturbance",
    "Kidnapping"
];
// Base danger weight per crime type (used in triage + hotspot weighting)
const TYPE_WEIGHT = {
    "Armed Robbery": 9,
    Carjacking: 8,
    Kidnapping: 10,
    Assault: 7,
    Burglary: 6,
    "Drug Offense": 5,
    Theft: 4,
    Fraud: 3,
    Vandalism: 3,
    "Public Disturbance": 2
};
function triage(type, severity) {
    const base = TYPE_WEIGHT[type] ?? 3;
    // severity 1..5 -> multiplier
    const score = Math.round(base * (0.6 + severity * 0.28) * 5);
    let priority;
    let recommendation;
    let eta;
    if (score >= 78) {
        priority = "critical";
        recommendation = "Dispatch armed response unit immediately. Alert nearest patrol and notify command center.";
        eta = "0-5 min";
    } else if (score >= 55) {
        priority = "high";
        recommendation = "Dispatch patrol unit as a priority. Keep reporter on the line for updates.";
        eta = "5-15 min";
    } else if (score >= 32) {
        priority = "medium";
        recommendation = "Queue for the next available patrol. Log details and monitor the area.";
        eta = "15-45 min";
    } else {
        priority = "low";
        recommendation = "Record for follow-up. Add to daily community patrol review.";
        eta = "1-4 hrs";
    }
    return {
        priority,
        score,
        recommendation,
        eta
    };
}
const PRIORITY_ORDER = [
    "critical",
    "high",
    "medium",
    "low"
];
const PRIORITY_WEIGHT = {
    critical: 4,
    high: 3,
    medium: 2,
    low: 1
};
function analyzeHotspots(points) {
    const CELL = 0.0065; // ~700m
    const cells = new Map();
    for (const p of points){
        const gx = Math.floor(p.lat / CELL);
        const gy = Math.floor(p.lng / CELL);
        const key = `${gx}:${gy}`;
        const cell = cells.get(key) ?? {
            sumLat: 0,
            sumLng: 0,
            count: 0,
            weight: 0,
            types: {}
        };
        cell.sumLat += p.lat;
        cell.sumLng += p.lng;
        cell.count += 1;
        const pw = PRIORITY_WEIGHT[p.priority] ?? 2;
        cell.weight += pw * (0.5 + p.severity * 0.1);
        cell.types[p.type] = (cell.types[p.type] ?? 0) + 1;
        cells.set(key, cell);
    }
    const results = [];
    for (const cell of cells.values()){
        if (cell.count < 2) continue; // need a cluster
        const topTypes = Object.entries(cell.types).sort((a, b)=>b[1] - a[1]).slice(0, 3).map(([t])=>t);
        let level = "low";
        if (cell.weight >= 7) level = "high";
        else if (cell.weight >= 4) level = "medium";
        results.push({
            lat: cell.sumLat / cell.count,
            lng: cell.sumLng / cell.count,
            count: cell.count,
            weight: Math.round(cell.weight * 10) / 10,
            radius: Math.min(900, 300 + cell.count * 70),
            level,
            topTypes
        });
    }
    return results.sort((a, b)=>b.weight - a.weight);
}
const PATROL_ROUTES = [
    {
        id: "route-a",
        name: "Route A — CBD & Avenues",
        color: "#2563eb",
        waypoints: [
            {
                lat: -17.8292,
                lng: 31.0522
            },
            {
                lat: -17.8252,
                lng: 31.0475
            },
            {
                lat: -17.8189,
                lng: 31.0433
            },
            {
                lat: -17.8151,
                lng: 31.0512
            },
            {
                lat: -17.8215,
                lng: 31.0585
            },
            {
                lat: -17.8292,
                lng: 31.0522
            }
        ]
    },
    {
        id: "route-b",
        name: "Route B — Mbare & Southern Ring",
        color: "#f97316",
        waypoints: [
            {
                lat: -17.8292,
                lng: 31.0522
            },
            {
                lat: -17.8451,
                lng: 31.0389
            },
            {
                lat: -17.8564,
                lng: 31.0301
            },
            {
                lat: -17.8611,
                lng: 31.0455
            },
            {
                lat: -17.8489,
                lng: 31.0603
            },
            {
                lat: -17.8292,
                lng: 31.0522
            }
        ]
    }
];
function haversineKm(a, b) {
    const R = 6371;
    const dLat = (b.lat - a.lat) * Math.PI / 180;
    const dLng = (b.lng - a.lng) * Math.PI / 180;
    const lat1 = a.lat * Math.PI / 180;
    const lat2 = b.lat * Math.PI / 180;
    const h = Math.sin(dLat / 2) ** 2 + Math.cos(lat1) * Math.cos(lat2) * Math.sin(dLng / 2) ** 2;
    return 2 * R * Math.asin(Math.sqrt(h));
}
function routeLengthKm(route) {
    let total = 0;
    for(let i = 1; i < route.waypoints.length; i++){
        total += haversineKm(route.waypoints[i - 1], route.waypoints[i]);
    }
    return Math.round(total * 100) / 100;
}
}),
"[project]/crime-watch-ui/extracted/src/app/api/seed/route.ts [app-route] (ecmascript)", ((__turbopack_context__) => {
"use strict";

return __turbopack_context__.a(async (__turbopack_handle_async_dependencies__, __turbopack_async_result__) => { try {

__turbopack_context__.s([
    "POST",
    ()=>POST,
    "dynamic",
    ()=>dynamic
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$crime$2d$watch$2d$ui$2f$extracted$2f$src$2f$db$2f$index$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/crime-watch-ui/extracted/src/db/index.ts [app-route] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$crime$2d$watch$2d$ui$2f$extracted$2f$src$2f$db$2f$schema$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/crime-watch-ui/extracted/src/db/schema.ts [app-route] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$crime$2d$watch$2d$ui$2f$extracted$2f$src$2f$lib$2f$auth$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/crime-watch-ui/extracted/src/lib/auth.ts [app-route] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$crime$2d$watch$2d$ui$2f$extracted$2f$src$2f$lib$2f$crime$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/crime-watch-ui/extracted/src/lib/crime.ts [app-route] (ecmascript)");
var __turbopack_async_dependencies__ = __turbopack_handle_async_dependencies__([
    __TURBOPACK__imported__module__$5b$project$5d2f$crime$2d$watch$2d$ui$2f$extracted$2f$src$2f$db$2f$index$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__,
    __TURBOPACK__imported__module__$5b$project$5d2f$crime$2d$watch$2d$ui$2f$extracted$2f$src$2f$lib$2f$auth$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__
]);
[__TURBOPACK__imported__module__$5b$project$5d2f$crime$2d$watch$2d$ui$2f$extracted$2f$src$2f$db$2f$index$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__, __TURBOPACK__imported__module__$5b$project$5d2f$crime$2d$watch$2d$ui$2f$extracted$2f$src$2f$lib$2f$auth$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__] = __turbopack_async_dependencies__.then ? (await __turbopack_async_dependencies__)() : __turbopack_async_dependencies__;
;
;
;
;
const dynamic = "force-dynamic";
// Extended Harare suburb clusters with realistic coordinates
const CLUSTERS = [
    {
        name: "CBD",
        lat: -17.8292,
        lng: 31.0522,
        n: 28
    },
    {
        name: "Mbare",
        lat: -17.8564,
        lng: 31.0301,
        n: 24
    },
    {
        name: "Avenues",
        lat: -17.8189,
        lng: 31.0433,
        n: 18
    },
    {
        name: "Highfield",
        lat: -17.8721,
        lng: 31.0022,
        n: 20
    },
    {
        name: "Avondale",
        lat: -17.8016,
        lng: 31.0389,
        n: 14
    },
    {
        name: "Waterfalls",
        lat: -17.8901,
        lng: 31.0555,
        n: 16
    },
    {
        name: "Borrowdale",
        lat: -17.7501,
        lng: 31.0889,
        n: 12
    },
    {
        name: "Budiriro",
        lat: -17.8626,
        lng: 31.0097,
        n: 14
    },
    {
        name: "Glen Norah",
        lat: -17.8473,
        lng: 30.9961,
        n: 12
    },
    {
        name: "Kuwadzana",
        lat: -17.7968,
        lng: 30.9822,
        n: 10
    },
    {
        name: "Kuwadzana Ext",
        lat: -17.7922,
        lng: 30.9766,
        n: 8
    },
    {
        name: "Dzivarasekwa",
        lat: -17.8012,
        lng: 30.9689,
        n: 10
    },
    {
        name: "Hatfield",
        lat: -17.8812,
        lng: 31.0944,
        n: 9
    },
    {
        name: "Mount Pleasant",
        lat: -17.7685,
        lng: 31.0449,
        n: 9
    },
    {
        name: "Marlborough",
        lat: -17.7523,
        lng: 31.0099,
        n: 7
    },
    {
        name: "Greendale",
        lat: -17.8101,
        lng: 31.1193,
        n: 8
    },
    {
        name: "Southerton",
        lat: -17.8512,
        lng: 31.0211,
        n: 11
    },
    {
        name: "Arcadia",
        lat: -17.8391,
        lng: 31.0677,
        n: 9
    },
    {
        name: "Eastlea",
        lat: -17.8133,
        lng: 31.0722,
        n: 8
    },
    {
        name: "Belvedere",
        lat: -17.8289,
        lng: 31.0199,
        n: 8
    }
];
const REPORTERS = [
    "Tendai Moyo",
    "Rudo Sibanda",
    "Farai Chitepo",
    "Nyasha Dube",
    "Tinashe Makoni",
    "Chipo Zulu",
    "Blessing Ncube",
    "Kuda Mutasa",
    "Simba Chigwada",
    "Mutsa Gumbo",
    "Tafara Hove",
    "Ruvimbo Dziva"
];
const INCIDENT_DESCRIPTIONS = {
    "Armed Robbery": [
        "Armed suspects demanded cash and valuables at gunpoint.",
        "Group of armed men stormed the premises, took electronics and cash.",
        "Victim was held at gunpoint near the bus stop; phone and wallet stolen.",
        "Armed robbers targeted a delivery vehicle, fled with goods."
    ],
    "Assault": [
        "Victim sustained injuries after being attacked by unknown assailants.",
        "Physical altercation escalated; victim taken to hospital.",
        "Domestic assault reported by neighbours who heard screaming.",
        "Bar fight resulted in serious injuries to two individuals."
    ],
    "Burglary": [
        "Residence broken into while occupants were away; valuables missing.",
        "Office premises burgled overnight; computers and safe compromised.",
        "Break-in through rear window; jewellery and electronics stolen.",
        "Storage unit forced open; construction equipment taken."
    ],
    "Carjacking": [
        "Vehicle hijacked at traffic lights; driver forced out at knifepoint.",
        "Parked car stolen from shopping centre car park.",
        "Armed carjacking on a residential driveway during morning hours.",
        "Ride-share driver's vehicle taken by passengers posing as clients."
    ],
    "Theft": [
        "Pickpocketing reported in a crowded market area.",
        "Mobile phone snatched from pedestrian's hand on the street.",
        "Bag stolen from restaurant table while victim was distracted.",
        "Bicycle taken from outside a shop; chain was cut."
    ],
    "Vandalism": [
        "Public property defaced with graffiti and minor fire damage.",
        "Several vehicles had windows smashed along the street overnight.",
        "Park benches and signage destroyed near the community hall.",
        "School perimeter wall damaged; stones thrown at classroom windows."
    ],
    "Drug Offense": [
        "Suspected drug dealing activity in abandoned building.",
        "Individual arrested with substantial quantity of illegal substances.",
        "Drug paraphernalia found near the sports ground.",
        "Neighbourhood tip-off about a house being used for drug distribution."
    ],
    "Fraud": [
        "Elderly resident targeted by phone scam; bank details compromised.",
        "Fake investment scheme discovered operating in the area.",
        "Identity theft case; fraudulent loan taken in victim's name.",
        "Counterfeit currency being circulated at informal market stalls."
    ],
    "Public Disturbance": [
        "Loud party escalated into a public disturbance; police called.",
        "Street vendor dispute turned violent, blocking traffic.",
        "Protest gathering near government offices; minor injuries.",
        "Drunk and disorderly behaviour outside a nightclub."
    ],
    "Kidnapping": [
        "Child approached by strangers near school; parent intervened.",
        "Businessman abducted briefly, released after family paid ransom.",
        "Attempted kidnapping of a teenager on the way home; escaped.",
        "Suspicious vehicle following students reported to authorities."
    ]
};
function rand(seed) {
    const x = Math.sin(seed) * 10000;
    return x - Math.floor(x);
}
async function POST() {
    // Seed demo users (idempotent)
    const existingUsers = await __TURBOPACK__imported__module__$5b$project$5d2f$crime$2d$watch$2d$ui$2f$extracted$2f$src$2f$db$2f$index$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__["db"].select().from(__TURBOPACK__imported__module__$5b$project$5d2f$crime$2d$watch$2d$ui$2f$extracted$2f$src$2f$db$2f$schema$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__["users"]).limit(1);
    if (!existingUsers[0]) {
        await __TURBOPACK__imported__module__$5b$project$5d2f$crime$2d$watch$2d$ui$2f$extracted$2f$src$2f$db$2f$index$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__["db"].insert(__TURBOPACK__imported__module__$5b$project$5d2f$crime$2d$watch$2d$ui$2f$extracted$2f$src$2f$db$2f$schema$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__["users"]).values([
            {
                name: "Officer Chikwava",
                email: "officer@harare.gov.zw",
                password: (0, __TURBOPACK__imported__module__$5b$project$5d2f$crime$2d$watch$2d$ui$2f$extracted$2f$src$2f$lib$2f$auth$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__["hashPassword"])("password123"),
                role: "officer",
                token: (0, __TURBOPACK__imported__module__$5b$project$5d2f$crime$2d$watch$2d$ui$2f$extracted$2f$src$2f$lib$2f$auth$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__["generateToken"])()
            },
            {
                name: "Command Admin",
                email: "admin@harare.gov.zw",
                password: (0, __TURBOPACK__imported__module__$5b$project$5d2f$crime$2d$watch$2d$ui$2f$extracted$2f$src$2f$lib$2f$auth$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__["hashPassword"])("password123"),
                role: "admin",
                token: (0, __TURBOPACK__imported__module__$5b$project$5d2f$crime$2d$watch$2d$ui$2f$extracted$2f$src$2f$lib$2f$auth$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__["generateToken"])()
            },
            {
                name: "Tendai Moyo",
                email: "community@harare.gov.zw",
                password: (0, __TURBOPACK__imported__module__$5b$project$5d2f$crime$2d$watch$2d$ui$2f$extracted$2f$src$2f$lib$2f$auth$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__["hashPassword"])("password123"),
                role: "community",
                token: (0, __TURBOPACK__imported__module__$5b$project$5d2f$crime$2d$watch$2d$ui$2f$extracted$2f$src$2f$lib$2f$auth$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__["generateToken"])()
            }
        ]);
    }
    const existingIncidents = await __TURBOPACK__imported__module__$5b$project$5d2f$crime$2d$watch$2d$ui$2f$extracted$2f$src$2f$db$2f$index$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__["db"].select().from(__TURBOPACK__imported__module__$5b$project$5d2f$crime$2d$watch$2d$ui$2f$extracted$2f$src$2f$db$2f$schema$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__["incidents"]).limit(1);
    if (!existingIncidents[0]) {
        const rows = [];
        let seed = 1;
        for (const c of CLUSTERS){
            for(let i = 0; i < c.n; i++){
                const lat = c.lat + (rand(seed++) - 0.5) * 0.015;
                const lng = c.lng + (rand(seed++) - 0.5) * 0.015;
                const type = __TURBOPACK__imported__module__$5b$project$5d2f$crime$2d$watch$2d$ui$2f$extracted$2f$src$2f$lib$2f$crime$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__["CRIME_TYPES"][Math.floor(rand(seed++) * __TURBOPACK__imported__module__$5b$project$5d2f$crime$2d$watch$2d$ui$2f$extracted$2f$src$2f$lib$2f$crime$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__["CRIME_TYPES"].length)];
                const severity = 1 + Math.floor(rand(seed++) * 5);
                const t = (0, __TURBOPACK__imported__module__$5b$project$5d2f$crime$2d$watch$2d$ui$2f$extracted$2f$src$2f$lib$2f$crime$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__["triage"])(type, severity);
                // spread over 45 days
                const ageDays = Math.floor(rand(seed++) * 45);
                // random hour 0-23
                const hour = Math.floor(rand(seed++) * 24);
                // status spread
                const s = rand(seed++);
                const status = s < 0.45 ? "reported" : s < 0.70 ? "dispatched" : "resolved";
                // pick a description
                const descs = INCIDENT_DESCRIPTIONS[type] ?? [
                    `${type} incident in ${c.name}.`
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
                    createdAt: d
                });
            }
        }
        // batch insert
        for(let i = 0; i < rows.length; i += 80){
            await __TURBOPACK__imported__module__$5b$project$5d2f$crime$2d$watch$2d$ui$2f$extracted$2f$src$2f$db$2f$index$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__["db"].insert(__TURBOPACK__imported__module__$5b$project$5d2f$crime$2d$watch$2d$ui$2f$extracted$2f$src$2f$db$2f$schema$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__["incidents"]).values(rows.slice(i, i + 80));
        }
    }
    const totalUsers = await __TURBOPACK__imported__module__$5b$project$5d2f$crime$2d$watch$2d$ui$2f$extracted$2f$src$2f$db$2f$index$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__["db"].select().from(__TURBOPACK__imported__module__$5b$project$5d2f$crime$2d$watch$2d$ui$2f$extracted$2f$src$2f$db$2f$schema$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__["users"]);
    const totalIncidents = await __TURBOPACK__imported__module__$5b$project$5d2f$crime$2d$watch$2d$ui$2f$extracted$2f$src$2f$db$2f$index$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__["db"].select().from(__TURBOPACK__imported__module__$5b$project$5d2f$crime$2d$watch$2d$ui$2f$extracted$2f$src$2f$db$2f$schema$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__["incidents"]);
    return Response.json({
        seeded: true,
        users: totalUsers.length,
        incidents: totalIncidents.length,
        demoAccounts: [
            {
                role: "officer",
                email: "officer@harare.gov.zw",
                password: "password123"
            },
            {
                role: "admin",
                email: "admin@harare.gov.zw",
                password: "password123"
            },
            {
                role: "community",
                email: "community@harare.gov.zw",
                password: "password123"
            }
        ]
    });
}
__turbopack_async_result__();
} catch(e) { __turbopack_async_result__(e); } }, false);}),
];

//# sourceMappingURL=%5Broot-of-the-server%5D__0j696-w._.js.map