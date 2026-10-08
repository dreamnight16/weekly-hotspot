/**
 * 格物（Dianalyze）周报数据模型。
 *
 * 数据由 weekly-cli 流水线写入 src/data/weekly/*.json。仓库中同时存在两代结构：
 *   v3「证据层」：phase1 / phase2 / phase4 / phase5 + 断言核验 + 生成记录（2026-W31 起）
 *   v2「五阶段」：events + synthesis（2026-W21 ~ 2026-W29）
 * 本模块把两者归一为同一套只读视图，页面只消费这里的结果，不直接读取原始字段。
 */

export type Generation = 'v3' | 'v2';

export interface SourceGrade {
  reliability: string;
  credibility: number;
  rationale?: string;
}

export interface TimelineItem {
  id: string;
  time: string;
  title: string;
  description: string;
  evidenceRefs?: string[];
}

export interface EvidenceItem {
  id: string;
  sourceType: string;
  sourceName: string;
  sourceUrl?: string;
  content: string;
  authenticity: string;
  aiReason?: string;
  classBias?: string;
}

export interface EdgeItem {
  from: string;
  to: string;
  type: string;
  description: string;
}

export interface OppositeLaw {
  identity?: string;
  struggle?: string;
  particularity?: string;
  universality?: string;
}

export interface QuantityLaw {
  oldQualityNegated?: string;
  quantitativeDirection?: string;
  measure?: string;
  newQuality?: string;
  currentPhase?: string;
}

export interface NegationLaw {
  oldThing?: string;
  firstNegation?: string;
  internalNegation?: string;
  direction?: string;
  stageCharacteristics?: string;
}

export interface ReviewChallenge {
  challengeId: string;
  targetClaim: string;
  claimLocation?: string;
  weaknessType?: string;
  weaknessExplanation?: string;
  counterEvidence?: unknown[];
  alternativeInterpretations?: unknown[];
  conflictingLogicalSteps?: unknown[];
  resilienceAssessment?: {
    resilience?: string;
    conditionsForOriginalToStand?: string;
    requiredCorrection?: string;
  };
}

export interface AdversarialReview {
  adversarySummary?: string;
  challenges?: ReviewChallenge[];
  noWeakClaimsFound?: boolean;
  noWeakClaimsRationale?: string;
}

export interface CausalLoop {
  diagramId?: string;
  description?: string;
  nodes?: string[];
  positiveFeedbackLoops?: string[];
  negativeFeedbackLoops?: string[];
  keyLeveragePoints?: string[];
}

export interface DataValidation {
  validationCheck?: string;
  dataSource?: string;
  result?: string;
  issues?: string[];
  confidence?: string;
}

export interface WeekEvent {
  id: string;
  title: string;
  summary: string;
  /** v2 字段 */
  impactScore?: number;
  infoGainScore?: number;
  classAnalysis?: { classNature?: string; contradiction?: string; historicalContext?: string };
  dialecticalSummary?: string;
  timeline?: TimelineItem[];
  evidence?: EvidenceItem[];
  edges?: EdgeItem[];
  /** v3 字段 */
  sourceUrl?: string;
  materialContent?: string;
  isDirectExpression?: boolean;
  sourceGrade?: SourceGrade | null;
  unityOfOpposites?: OppositeLaw;
  quantityQuality?: QuantityLaw;
  negationOfNegation?: NegationLaw;
  dialecticalConfidence?: string;
  adversarialReview?: AdversarialReview;
  causalLoopDiagram?: CausalLoop;
  dataValidation?: DataValidation;
  phaseSummary?: string;
}

export interface ExcludedEvent {
  id: string;
  title: string;
  summary: string;
  exclusionReason: string;
}

export interface VerificationResult {
  claimId: string;
  claim: string;
  claimType?: string;
  verificationStatus?: string;
  independentSources?: string[];
  contradictorySources?: string[] | null;
  verificationNote?: string;
  confidence?: string;
}

export interface InformationGap {
  gapDescription: string;
  severity: string;
  possibleSources?: string;
}

export interface CorroborationRow {
  factStatement: string;
  sources?: string[];
  independentCount?: number;
  sourceDiversity?: string;
  crossConsistency?: string;
}

export interface AchResult {
  achId: string;
  proposition: string;
  eventId?: string;
  hypotheses?: Array<{
    hypothesisLabel: string;
    description: string;
    consistencyWithEvidence?: string;
    contradictionsWithEvidence?: string;
  }>;
}

export interface EmpiricalDossier {
  verificationSummary?: string;
  sourceGrades?: SourceGrade[];
  verificationResults?: VerificationResult[];
  informationGaps?: InformationGap[];
  achResults?: AchResult[];
  corroborationMatrix?: CorroborationRow[];
}

export interface ClassPosition {
  className: string;
  position?: string;
  coreInterest?: string;
  contradictions?: string[];
  relatedEventIds?: string[];
}

export interface InterestStructure {
  interestGroup: string;
  materialInterest?: string;
  expressionForm?: string;
  intensity?: number;
  relatedEventIds?: string[];
}

export interface ScoreDimension {
  id: string;
  name: string;
  score: number;
  confidence?: string;
  rationale?: string;
}

export interface Scorecard {
  eventId: string;
  eventTitle: string;
  compositeScore?: number;
  dimensions?: ScoreDimension[];
  informationSufficiency?: string;
  overallConfidence?: string;
  scoringSummary?: string;
}

export interface Hypothesis {
  hypothesisId: string;
  description: string;
  supportingEvidence?: string;
  contradictingEvidence?: string;
  assessedProbability?: number;
  relatedEventIds?: string[];
}

export interface EpochTheme {
  themeName: string;
  description?: string;
  relevanceToCurrentEvents?: string;
  relatedEventIds?: string[];
}

export interface HiddenConnection {
  connectionName: string;
  entityA?: string;
  entityB?: string;
  connectionMechanism?: string;
  significance?: string;
  relatedEventIds?: string[];
}

export interface HistoricalAnalogy {
  analogyName: string;
  historicalPeriod?: string;
  historicalEvent?: string;
  similarity?: string;
  difference?: string;
  lessonForToday?: string;
  relatedEventIds?: string[];
}

export interface SystemArchetype {
  archetypeType?: string;
  patternName: string;
  description?: string;
  structuralFeatures?: string;
  relatedEventIds?: string[];
}

export interface Scenario {
  scenarioId: string;
  title: string;
  description?: string;
  scenarioType?: string;
  probability?: number;
  keyAssumptions?: string[];
  earlySignals?: string[];
  relatedEventIds?: string[];
}

export interface WatchSignal {
  signalName: string;
  indicator?: string;
  threshold?: string;
  currentValue?: string;
  trend?: string;
  priority?: number;
  description?: string;
}

export interface Calibration {
  predictionSummary?: string;
  actualOutcome?: string;
  calibrationNote?: string;
  accuracyScore?: number | null;
}

export interface Phase1 {
  phaseSummary?: string;
  sourceQualityReport?: string;
  selectedEvents?: ExcludedEvent[];
  excludedEvents: ExcludedEvent[];
  dossiers: EmpiricalDossier[];
  empiricalVerified?: boolean;
  empiricalDegraded?: boolean;
}

export interface Phase2 {
  phaseSummary?: string;
  overallContradictionLandscape?: string;
  classPositions: ClassPosition[];
  interestStructures: InterestStructure[];
  competingHypotheses: Hypothesis[];
  scorecards: Scorecard[];
  nineDimScores?: Record<string, [number, number]>;
  empiricalVerified?: boolean;
  empiricalDegraded?: boolean;
}

export interface Phase4 {
  phaseSummary?: string;
  crossCuttingSynthesis?: string;
  epochThemes: EpochTheme[];
  hiddenConnections: HiddenConnection[];
  historicalAnalogies: HistoricalAnalogy[];
  systemArchetypes: SystemArchetype[];
  empiricalVerified?: boolean;
  empiricalDegraded?: boolean;
}

export interface Phase5 {
  overallJudgment?: string;
  practiceSignificance?: string;
  scenarios: Scenario[];
  signalsToWatch: WatchSignal[];
  calibration?: Calibration;
  empiricalVerified?: boolean;
  empiricalDegraded?: boolean;
}

export interface SynthesisTheme {
  name: string;
  description?: string;
  relatedEventIds?: string[];
  significance?: string;
}

export interface SynthesisTrend {
  name: string;
  description?: string;
  direction?: string;
  evidenceEventIds?: string[];
}

export interface ContradictionInMotion {
  contradiction: string;
  opposingForces?: string;
  eventsInvolved?: string[];
  currentState?: string;
  outlook?: string;
}

export interface Synthesis {
  weeklyNarrative?: string;
  crossCuttingThemes: SynthesisTheme[];
  trends: SynthesisTrend[];
  contradictionsInMotion: ContradictionInMotion[];
  globalAssessment?: string;
  dataGaps: string[];
}

export interface RunMeta {
  runId?: string;
  runDurationSeconds?: number;
  totalApiCost?: number;
  verificationPasses?: number;
  empiricalDegradations: string[];
  modelVersions?: { dialectical?: string; empirical?: string };
}

export interface Week {
  /** 期号，如 2026-W41 */
  id: string;
  /** 年份，如 2026 */
  year: string;
  /** 周序号，如 W41 */
  label: string;
  start: string;
  end: string;
  generation: Generation;
  events: WeekEvent[];
  /** 本期被排除的候选热点（仅 v3 记录） */
  excluded: ExcludedEvent[];
  synthesis?: Synthesis;
  phase1?: Phase1;
  phase2?: Phase2;
  phase4?: Phase4;
  phase5?: Phase5;
  meta?: RunMeta;
  /** 索引页使用的一句话摘要，取自本期真实文本 */
  lead: string;
}

const modules = import.meta.glob('../data/weekly/*.json', { eager: true });

const arr = <T,>(value: T[] | undefined | null): T[] => (Array.isArray(value) ? value : []);

function normalizeEvent(raw: any): WeekEvent {
  return {
    id: String(raw.id),
    title: raw.title ?? '',
    summary: raw.summary ?? '',
    impactScore: typeof raw.impactScore === 'number' ? raw.impactScore : undefined,
    infoGainScore: typeof raw.infoGainScore === 'number' ? raw.infoGainScore : undefined,
    classAnalysis: raw.classAnalysis ?? undefined,
    dialecticalSummary: raw.dialecticalSummary ?? undefined,
    timeline: arr(raw.timeline),
    evidence: arr(raw.evidence),
    edges: arr(raw.edges),
    sourceUrl: raw.sourceUrl ?? undefined,
    materialContent: raw.materialContent ?? undefined,
    isDirectExpression: raw.isDirectExpression,
    sourceGrade: raw.sourceGrade ?? null,
    unityOfOpposites: raw.unityOfOpposites ?? undefined,
    quantityQuality: raw.quantityQuality ?? undefined,
    negationOfNegation: raw.negationOfNegation ?? undefined,
    dialecticalConfidence: raw.dialecticalConfidence ?? undefined,
    adversarialReview: raw.adversarialReview ?? undefined,
    causalLoopDiagram: raw.causalLoopDiagram ?? undefined,
    dataValidation: raw.dataValidation ?? undefined,
    phaseSummary: raw.phaseSummary ?? undefined,
  };
}

function normalizeWeek(raw: any): Week {
  const id: string = raw.id;
  const events = arr<any>(raw.events).map(normalizeEvent);
  const phase1: Phase1 | undefined = raw.phase1
    ? {
        phaseSummary: raw.phase1.phaseSummary,
        sourceQualityReport: raw.phase1.sourceQualityReport,
        selectedEvents: arr(raw.phase1.selectedEvents),
        excludedEvents: arr(raw.phase1.excludedEvents),
        dossiers: arr(raw.phase1.empiricalSupplemental),
        empiricalVerified: raw.phase1.empiricalVerified,
        empiricalDegraded: raw.phase1.empiricalDegraded,
      }
    : undefined;
  const phase2: Phase2 | undefined = raw.phase2
    ? {
        phaseSummary: raw.phase2.phaseSummary,
        overallContradictionLandscape: raw.phase2.overallContradictionLandscape,
        classPositions: arr(raw.phase2.classPositions),
        interestStructures: arr(raw.phase2.interestStructures),
        competingHypotheses: arr(raw.phase2.competingHypotheses),
        scorecards: arr(raw.phase2.empiricalSupplemental),
        nineDimScores: raw.phase2.nineDimScores,
        empiricalVerified: raw.phase2.empiricalVerified,
        empiricalDegraded: raw.phase2.empiricalDegraded,
      }
    : undefined;
  const phase4: Phase4 | undefined = raw.phase4
    ? {
        phaseSummary: raw.phase4.phaseSummary,
        crossCuttingSynthesis: raw.phase4.crossCuttingSynthesis,
        epochThemes: arr(raw.phase4.epochThemes),
        hiddenConnections: arr(raw.phase4.hiddenConnections),
        historicalAnalogies: arr(raw.phase4.historicalAnalogies),
        systemArchetypes: arr(raw.phase4.systemArchetypes),
        empiricalVerified: raw.phase4.empiricalVerified,
        empiricalDegraded: raw.phase4.empiricalDegraded,
      }
    : undefined;
  const phase5: Phase5 | undefined = raw.phase5
    ? {
        overallJudgment: raw.phase5.overallJudgment,
        practiceSignificance: raw.phase5.practiceSignificance,
        scenarios: arr(raw.phase5.scenarios),
        signalsToWatch: arr(raw.phase5.signalsToWatch),
        calibration: raw.phase5.lastWeekCalibration ?? undefined,
        empiricalVerified: raw.phase5.empiricalVerified,
        empiricalDegraded: raw.phase5.empiricalDegraded,
      }
    : undefined;
  const synthesis: Synthesis | undefined = raw.synthesis
    ? {
        weeklyNarrative: raw.synthesis.weeklyNarrative,
        crossCuttingThemes: arr(raw.synthesis.crossCuttingThemes),
        trends: arr(raw.synthesis.trends),
        contradictionsInMotion: arr(raw.synthesis.contradictionsInMotion),
        globalAssessment: raw.synthesis.globalAssessment,
        dataGaps: arr<string>(raw.synthesis.dataGaps),
      }
    : undefined;
  const meta: RunMeta | undefined = raw.metadata
    ? {
        runId: raw.metadata.runId,
        runDurationSeconds: raw.metadata.runDuration,
        totalApiCost: raw.metadata.totalApiCost,
        verificationPasses: raw.metadata.verificationPasses,
        empiricalDegradations: arr<string>(raw.metadata.empiricalDegradations),
        modelVersions: raw.metadata.modelVersions,
      }
    : undefined;

  return {
    id,
    year: id.slice(0, 4),
    label: id.slice(5),
    start: raw.weekStart,
    end: raw.weekEnd,
    generation: phase1 ? 'v3' : 'v2',
    events,
    excluded: phase1?.excludedEvents ?? [],
    synthesis,
    phase1,
    phase2,
    phase4,
    phase5,
    meta,
    lead: phase1?.phaseSummary || phase4?.crossCuttingSynthesis || synthesis?.weeklyNarrative || phase5?.overallJudgment || '',
  };
}

/** 全部期次，按期号倒序（最新在前）。 */
export const weeks: Week[] = Object.values(modules)
  .map((mod: any) => normalizeWeek(mod.default ?? mod))
  .sort((a, b) => b.id.localeCompare(a.id));

export const weekCount = weeks.length;
export const eventCount = weeks.reduce((n, w) => n + w.events.length, 0);
export const generationCount = new Set(weeks.map((w) => w.generation)).size;
export const latest = weeks[0];

/** 数据覆盖区间（首期开始日 → 末周结束日）。 */
export const firstStart = weeks.length ? weeks[weeks.length - 1].start : '';
export const lastEnd = weeks.length ? latest.end : '';

export function daysBetween(from: string, to: string): number {
  const ms = Date.parse(to + 'T00:00:00Z') - Date.parse(from + 'T00:00:00Z');
  return Math.round(ms / 86_400_000) + 1;
}

export function findWeek(id: string): Week | undefined {
  return weeks.find((w) => w.id.toLowerCase() === id.toLowerCase());
}

/** 期次在倒序列表中的前后邻居，用于详情页导航。 */
export function neighbours(id: string): { prev?: Week; next?: Week } {
  const i = weeks.findIndex((w) => w.id === id);
  if (i === -1) return {};
  return { prev: weeks[i + 1], next: weeks[i - 1] };
}

export interface SummaryBlock {
  label: string;
  source: string;
  text: string;
}

/** 本期综合文字。v3 取 Phase 4/5 的综合与总体判断，v2 取叙事与总体估计。 */
export function summaryBlocks(week: Week): SummaryBlock[] {
  const pairs: Array<[string, string, string | undefined]> =
    week.generation === 'v3'
      ? [
          ['跨事件综合', 'Phase 4 输出', week.phase4?.crossCuttingSynthesis],
          ['总体判断', 'Phase 5 输出', week.phase5?.overallJudgment],
        ]
      : [
          ['本周叙事', '跨事件综合输出', week.synthesis?.weeklyNarrative],
          ['总体估计', '跨事件综合输出', week.synthesis?.globalAssessment],
        ];
  return pairs
    .filter(([, , text]) => typeof text === 'string' && text.trim().length > 0)
    .map(([label, source, text]) => ({ label, source, text: text as string }));
}

/** 事件 id → 标题。既解析本期分析事件，也解析被排除的候选热点。 */
export function eventTitles(week: Week): Map<string, { title: string; href?: string }> {
  const map = new Map<string, { title: string; href?: string }>();
  for (const e of week.excluded) map.set(String(e.id), { title: e.title });
  for (const e of week.events) map.set(String(e.id), { title: e.title, href: `#evt-${e.id}` });
  return map;
}

export function blogPostUrl(id: string): string {
  return `https://blog.dreamnight.net.cn/posts/${id.toLowerCase()}/`;
}
