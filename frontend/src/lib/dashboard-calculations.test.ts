import {
  computeComplianceDeduction,
  computeContribution,
  computeDashboard,
  computeStreamScore,
  type DashboardComputationInput,
  type StreamBlueprint,
} from "@/lib/dashboard-calculations";

const baseStream: StreamBlueprint = {
  code: "EAF",
  name: "Equivalent Availability Factor",
  kind: "quantitative",
  pillar: "I",
  unit: "%",
  formula: "positive",
  polarity: "positif",
  actualValue: 88.6,
  targetValue: 85,
  weight: 6,
  note: "positive KPI",
};

describe("dashboard calculations", () => {
  it("scores positive quantitative streams as actual / target", () => {
    expect(computeStreamScore(baseStream)).toBeCloseTo(104.24, 2);
    expect(computeContribution(104.24, 6)).toBeCloseTo(6.25, 2);
  });

  it("scores negative quantitative streams with inverted polarity", () => {
    expect(
      computeStreamScore({
        ...baseStream,
        code: "EFOR",
        formula: "negative",
        polarity: "negatif",
        actualValue: 3.7,
        targetValue: 4.2,
      }),
    ).toBeCloseTo(111.9, 2);
  });

  it("scores maturity and compliance streams on the 0-4 rubric scale", () => {
    expect(
      computeStreamScore({
        ...baseStream,
        code: "OUTAGE",
        kind: "maturity",
        unit: "Level 0-4",
        formula: "rubric",
        polarity: "rubric",
        actualValue: 3.42,
        targetValue: 3.25,
        weight: 25,
      }),
    ).toBeCloseTo(85.5, 2);
  });

  it("computes compliance as a controlled NKO deduction", () => {
    expect(
      computeComplianceDeduction(
        {
          ...baseStream,
          code: "SMAP",
          kind: "compliance",
          unit: "Level 0-4",
          formula: "compliance",
          polarity: "rubric",
          actualValue: 3.1,
          targetValue: 3.5,
          weight: 0,
        },
        6.9,
      ),
    ).toBeCloseTo(2.76, 2);
  });

  it("reconciles the dummy dashboard to the worked example NKO", () => {
    const input: DashboardComputationInput = {
      periode: "Semester 2 2025",
      updatedAt: "12 Mei 2026 00:02 WIB",
      changedIndikator: "EAF",
      forecastDelta: 0.82,
      complianceDeductionFactor: 6.9,
      pillars: [
        { code: "I", name: "Economic & Social Value", weight: 46, trend: 1.42 },
        { code: "II", name: "Model Business Innovation", weight: 25, trend: 0.88 },
        { code: "III", name: "Technology Leadership", weight: 6, trend: 0.18 },
        { code: "IV", name: "Energize Investment", weight: 8, trend: -0.31 },
        { code: "V", name: "Unleash Talent", weight: 15, trend: 0.54 },
      ],
      pillarComplements: {
        I: 35.95,
        II: 4.99,
        III: 6.22,
        IV: 8.37,
        V: 16.25,
      },
      streams: [
        baseStream,
        {
          ...baseStream,
          code: "EFOR",
          name: "Equivalent Forced Outage Rate",
          formula: "negative",
          polarity: "negatif",
          actualValue: 3.7,
          targetValue: 4.2,
        },
        {
          ...baseStream,
          code: "OUTAGE",
          name: "Outage Management",
          kind: "maturity",
          pillar: "II",
          unit: "Level 0-4",
          formula: "rubric",
          polarity: "rubric",
          actualValue: 3.42,
          targetValue: 3.25,
          weight: 25,
        },
        {
          ...baseStream,
          code: "SMAP",
          name: "Sistem Manajemen Anti Penyuapan",
          kind: "compliance",
          pillar: "VI",
          unit: "Level 0-4",
          formula: "compliance",
          polarity: "rubric",
          actualValue: 3.1,
          targetValue: 3.5,
          weight: 0,
        },
      ],
    };

    const { snapshot, streams } = computeDashboard(input);

    expect(snapshot.grossPillar).toBe(106.12);
    expect(snapshot.complianceDeduction).toBe(2.76);
    expect(snapshot.nkoTotal).toBe(103.36);
    expect(snapshot.forecast).toBe(104.18);
    expect(streams.find((stream) => stream.code === "SMAP")?.deduction).toBe(2.76);
  });
});
