export type StreamKind = "quantitative" | "maturity" | "hybrid" | "compliance";

export type Polarity = "positif" | "negatif" | "range" | "rubric";

export type StreamBlueprint = {
  code: string;
  name: string;
  kind: StreamKind;
  pillar: string;
  unit: string;
  formula: string;
  polarity: Polarity;
  actualValue: number;
  targetValue: number;
  weight: number;
  note: string;
};

export type ComputedStream = StreamBlueprint & {
  actual: string;
  target: string;
  score: number;
  contribution: number;
  deduction: number;
};

export type PillarSummary = {
  code: string;
  name: string;
  weight: number;
  contribution: number;
  trend: number;
  status: "stabil" | "naik" | "turun";
};

export type DashboardSnapshot = {
  periode: string;
  nkoTotal: number;
  grossPillar: number;
  complianceDeduction: number;
  forecast: number;
  updatedAt: string;
  changedIndikator: string;
};

export type PillarDefinition = {
  code: string;
  name: string;
  weight: number;
  trend: number;
};

export type DashboardComputationInput = {
  periode: string;
  updatedAt: string;
  changedIndikator: string;
  streams: StreamBlueprint[];
  pillars: PillarDefinition[];
  pillarComplements: Record<string, number>;
  forecastDelta: number;
  complianceDeductionFactor: number;
};

export function round2(value: number) {
  return Math.round((value + Number.EPSILON) * 100) / 100;
}

export function computeStreamScore(stream: StreamBlueprint) {
  if (stream.kind === "maturity" || stream.kind === "compliance" || stream.polarity === "rubric") {
    return (stream.actualValue / 4) * 100;
  }

  if (stream.polarity === "negatif") {
    return (2 - stream.actualValue / stream.targetValue) * 100;
  }

  return (stream.actualValue / stream.targetValue) * 100;
}

export function computeContribution(score: number, weight: number) {
  return (score / 100) * weight;
}

export function computeComplianceDeduction(stream: StreamBlueprint, factor: number) {
  if (stream.kind !== "compliance") return 0;
  return Math.max(0, stream.targetValue - stream.actualValue) * factor;
}

export function formatStreamValue(stream: StreamBlueprint, value: number) {
  if (stream.unit === "%") {
    return `${value.toLocaleString("id-ID", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}%`;
  }

  return value.toLocaleString("id-ID", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

export function computeDashboard(input: DashboardComputationInput) {
  const streams: ComputedStream[] = input.streams.map((stream) => {
    const score = round2(computeStreamScore(stream));
    return {
      ...stream,
      actual: formatStreamValue(stream, stream.actualValue),
      target: formatStreamValue(stream, stream.targetValue),
      score,
      contribution: round2(computeContribution(score, stream.weight)),
      deduction: round2(computeComplianceDeduction(stream, input.complianceDeductionFactor)),
    };
  });

  const pillars: PillarSummary[] = input.pillars.map((pillar) => {
    const directContribution = streams
      .filter((stream) => stream.pillar === pillar.code && stream.kind !== "compliance")
      .reduce((total, stream) => total + stream.contribution, 0);
    const contribution = round2(directContribution + (input.pillarComplements[pillar.code] ?? 0));
    return {
      ...pillar,
      contribution,
      status: pillar.trend < -0.05 ? "turun" : pillar.trend > 0.05 ? "naik" : "stabil",
    };
  });

  const grossPillar = round2(
    pillars
      .filter((pillar) => pillar.code !== "VI")
      .reduce((total, pillar) => total + pillar.contribution, 0),
  );
  const complianceDeduction = round2(
    input.streams.reduce(
      (total, stream) => total + computeComplianceDeduction(stream, input.complianceDeductionFactor),
      0,
    ),
  );
  const nkoTotal = round2(grossPillar - complianceDeduction);

  const snapshot: DashboardSnapshot = {
    periode: input.periode,
    nkoTotal,
    grossPillar,
    complianceDeduction,
    forecast: round2(nkoTotal + input.forecastDelta),
    updatedAt: input.updatedAt,
    changedIndikator: input.changedIndikator,
  };

  return { streams, pillars, snapshot };
}
