// TypeScript types that align with backend/schemas.py

export enum ReviewStatus {
    Pending = "pending",
    Accepted = "accepted",
    Rejected = "rejected",
}

export enum ThreatCategory {
    Spoofing = "spoofing",
    Tampering = "tampering",
    Repudiation = "repudiation",
    InformationDisclosure = "information_disclosure",
    DenialOfService = "denial_of_service",
    ElevationOfPrivilege = "elevation_of_privilege",
    Other = "other",
}

export enum Likert {
    VeryLow = 1,
    Low = 2,
    Medium = 3,
    High = 4,
    VeryHigh = 5,
}

// Core schemas with UUIDs
export interface Attacker {
    id: string; // UUID
    description: string;
    skill_level: Likert;
    access_level: Likert;
    prob_of_attack: number; // 0.0 to 1.0
}

export interface EntryPoint {
    id: string; // UUID
    name: string;
    description: string;
    prob_of_entry: number; // 0.0 to 1.0
    difficulty_of_entry: Likert;
}

export interface Asset {
    id: string; // UUID
    name: string;
    description: string;
    failure_modes: string[];
}

export interface ContextEnumeration {
    attackers: Attacker[];
    entry_points: EntryPoint[];
    assets: Asset[];
    assumptions: string[];
    questions: string[];
    answers: string[];
}

// Ranking schemas for review
export interface EntryPointRanking {
    entry_id: string; // UUID
    likelihood: Likert;
    reviewer: string;
    status: ReviewStatus;
    comments?: string;
}

export interface AssetValueRanking {
    asset_id: string; // UUID
    value: Likert;
    reviewer: string;
    status: ReviewStatus;
    comments?: string;
}

export interface AttackerProfileRanking {
    attacker_id: string; // UUID
    threat_level: Likert;
    reviewer: string;
    status: ReviewStatus;
    comments?: string;
}

// Request schemas
export interface ContextRequest {
    textual_dfd: string;
    extra_prompt?: string;
    questions: string[];
    answers: string[];
}

export interface VerifiedContext {
    textual_dfd: string;
    attackers: AttackerProfileRanking[];
    entry_points: EntryPointRanking[];
    assets: AssetValueRanking[];
    assumptions: string[];
    questions: string[];
    answers: string[];
}

// Threat schemas
export interface ThreatChain {
    name: string;
    chain: string[];
    category: ThreatCategory;
    description: string;
    mitre_atlas: string;
    mitre_attack: string;
    mitigations: string[];
}

export interface ThreatEnumeration {
    threat_chains: ThreatChain[];
}

// Helper types
export type AppState = 'input' | 'review' | 'threats'; 