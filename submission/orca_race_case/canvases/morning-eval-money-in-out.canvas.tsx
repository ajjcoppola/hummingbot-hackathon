import {
  Callout,
  Card,
  CardBody,
  CardHeader,
  Divider,
  Grid,
  H1,
  H2,
  LineChart,
  Pill,
  Row,
  Stack,
  Stat,
  Table,
  Text,
} from "cursor/canvas";

/** Money-in: verified fund 100.25 USDC + 0.16535 SOL @ deposit mark 116.77 */
const CAPITAL_IN = 119.56;

const LIVE = {
  equity: 121.3,
  vsIn: 1.74,
  vsHodl: 0.95,
  price: 121.53,
  inRange: false,
  lp: "gvVUtyJs…",
  band: "[114.56, 116.31]",
  freeSol: 0.175,
  freeUsdc: 60.21,
  lpUsdc: 39.81,
  bot: "…213341",
  stuckHours: 8.6,
};

const OVERNIGHT = {
  hours: 18.9,
  botUptime: 100,
  rebalsTotal: 7,
  rebalsOvernight: 2,
  inRangePct: 46.1,
  overnightInRangePct: 14.5,
  cleanDMtm: 0.59,
  feeEndUsdc: 0.015,
  maxFeeUsdc: 0.155,
  solDelta: 0.083,
};

/** Hourly clean marks — strategy equity vs HODL of funded bag */
const HOURLY = [
  { t: "21:58", equity: 120.22, hodl: 119.59 },
  { t: "22:59", equity: 119.94, hodl: 119.52 },
  { t: "23:59", equity: 120.26, hodl: 119.6 },
  { t: "00:58", equity: 120.42, hodl: 119.66 },
  { t: "01:59", equity: 120.42, hodl: 119.67 },
  { t: "02:58", equity: 120.56, hodl: 119.58 },
  { t: "03:59", equity: 120.53, hodl: 119.56 },
  { t: "04:57", equity: 120.73, hodl: 119.56 },
  { t: "05:58", equity: 120.4, hodl: 119.5 },
  { t: "06:59", equity: 120.38, hodl: 119.47 },
  { t: "07:58", equity: 120.39, hodl: 119.49 },
  { t: "08:59", equity: 120.56, hodl: 119.65 },
  { t: "09:59", equity: 120.74, hodl: 119.82 },
  { t: "10:58", equity: 120.89, hodl: 119.96 },
  { t: "11:59", equity: 121.17, hodl: 120.22 },
  { t: "12:58", equity: 121.17, hodl: 120.22 },
  { t: "13:58", equity: 120.95, hodl: 120.02 },
  { t: "14:57", equity: 121.1, hodl: 120.16 },
  { t: "15:58", equity: 121.0, hodl: 120.06 },
  { t: "16:32", equity: 121.3, hodl: 120.35 },
];

const FACTS = [
  ["Bot uptime", "100%"],
  ["Window", "~18.9 h (T011)"],
  ["Close→open (total / overnight)", "7 / 2"],
  ["In-range (full / overnight)", "46% / 15%"],
  ["Clean Δ MTM overnight", "+$0.59"],
  ["Pending fees now", "~$0.015 USDC"],
  ["Free SOL Δ (T011)", "+0.083 (rent/refunds)"],
  ["Stuck OOR past limit", `~${LIVE.stuckHours}h — ops issue`],
];

const DECISION = [
  ["Lane", "Cup primary (finals Oct 1)"],
  ["Blocker first", "Unstick LP (soft-restart → recycle if needed)"],
  ["Next trial after unstuck", "T012 — C1 width 1.5 → 1.0"],
  ["YAML", "position_width_pct: 1.0; keep threshold 0.05"],
  ["Success (4–8h)", "n_rebals≥2, in-range>40%, no >1h past-limit HOLD"],
];

export default function MorningEvalMoneyInOut() {
  return (
    <Stack gap={24} style={{ padding: 24, maxWidth: 980 }}>
      <Stack gap={8}>
        <H1>Morning eval — money in → money out</H1>
        <Text tone="secondary">
          Funded 100.25 USDC + 0.16535 SOL @ $116.77 deposit mark = ${CAPITAL_IN}{" "}
          in. Marks = wallet + LP + pending fees. HODL = same funded bag marked
          at spot. T011 through 2026-09-25 16:32Z.
        </Text>
        <Row gap={8} style={{ flexWrap: "wrap" }}>
          <Pill tone="warning">OOR past limit ~{LIVE.stuckHours}h</Pill>
          <Pill tone="success">bot up 100%</Pill>
          <Pill tone="info">+${LIVE.vsIn} vs money-in</Pill>
          <Pill>+${LIVE.vsHodl} vs HODL bag</Pill>
        </Row>
      </Stack>

      <Grid columns={4} gap={12}>
        <Stat value={`$${CAPITAL_IN}`} label="Money in (deposit mark)" />
        <Stat value={`$${LIVE.equity}`} label="Money out (now)" tone="success" />
        <Stat value={`+$${LIVE.vsIn}`} label="vs money-in" tone="success" />
        <Stat value={`+$${LIVE.vsHodl}`} label="vs HODL funded bag" />
      </Grid>

      <Callout tone="warning" title="Ops before any param change">
        LP {LIVE.lp} band {LIVE.band} while spot {LIVE.price} (~4.5% above
        upper). Auto-close should have fired near ~116.37. Bot {LIVE.bot} still
        running — soft-restart first; adopt --recycle if still stuck. Do not
        tighten width while past-limit HOLD.
      </Callout>

      <Card>
        <CardHeader trailing={<Text size="small">USDC</Text>}>
          Strategy equity vs HODL funded bag
        </CardHeader>
        <CardBody>
          <LineChart
            categories={HOURLY.map((p) => p.t)}
            series={[
              {
                name: "Strategy (money out)",
                data: HOURLY.map((p) => p.equity),
                tone: "info",
              },
              {
                name: "HODL 100.25 USDC + 0.16535 SOL",
                data: HOURLY.map((p) => p.hodl),
                tone: "neutral",
              },
            ]}
            referenceLines={[
              {
                value: CAPITAL_IN,
                label: "Money in $119.56",
                tone: "warning",
              },
            ]}
            height={260}
          />
          <Text size="small" tone="secondary" style={{ marginTop: 8 }}>
            Source: T011 clean hourly marks (n_positions=1, equity $90–150).
            Flat overnight P&amp;L; SOL rally lifts both lines; strategy stays
            slightly above HODL while sitting 100% quote OOR.
          </Text>
        </CardBody>
      </Card>

      <Grid columns={2} gap={16}>
        <Card>
          <CardHeader>Section 0 — overnight facts</CardHeader>
          <CardBody>
            <Table
              headers={["Metric", "Value"]}
              rows={FACTS}
            />
          </CardBody>
        </Card>
        <Card>
          <CardHeader>Decision (Cup)</CardHeader>
          <CardBody>
            <Table headers={["Item", "Choice"]} rows={DECISION} />
            <Text size="small" tone="secondary" style={{ marginTop: 8 }}>
              Invest path would be I1 widen after unstick — not this morning if
              Cup is primary.
            </Text>
          </CardBody>
        </Card>
      </Grid>

      <Divider />

      <Stack gap={6}>
        <H2>Capital composition now</H2>
        <Text>
          Free {LIVE.freeSol} SOL + ${LIVE.freeUsdc} USDC · LP ${LIVE.lpUsdc}{" "}
          USDC (0 SOL) · pending fees ~${OVERNIGHT.feeEndUsdc}
        </Text>
        <Text size="small" tone="secondary">
          Not audited race P&amp;L. Ledger T011/T012. Docs:
          MORNING_EVAL_20260925.md
        </Text>
      </Stack>
    </Stack>
  );
}
