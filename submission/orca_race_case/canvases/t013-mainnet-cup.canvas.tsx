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

/** Money-in: 100.25 USDC + 0.16535 SOL at the $116.77 deposit mark. */
const CAPITAL_IN = 119.56;

/** Chain mark 2026-10-02 14:06Z. Includes position-NFT rent. Not a ledger row. */
const LIVE = {
  equity: 121.83,
  vsIn: 2.27,
  vsHodl: 1.35,
  hodl: 120.48,
  price: 122.34,
  inRange: true,
  widthPct: 16.08,
  lp: "78Spb3n7…",
  band: "[112.20, 131.77]",
  limits: "[112.14, 131.84]",
  limitsWide: "[111.64, 132.43]",
  freeSol: 0.121342,
  freeUsdc: 9.572834,
  lpSol: 0.36439,
  lpUsdc: 51.807842,
  rentSol: 0.008408,
  opened: "2026-10-02 05:47Z",
  quietHours: 8.3,
};

const REBALS = {
  total: 97,
  width15: 12,
  width10: 81,
  width16: 4,
  failedOpens: 8,
  collectFees: 96,
  lastTight: "2026-09-28 23:09Z",
  today: 1,
};

const DAYS = ["Sep 25", "Sep 26", "Sep 27", "Sep 28", "Sep 29", "Sep 30", "Oct 1", "Oct 2"];
const REBAL_15 = [12, 0, 0, 0, 0, 0, 0, 0];
const REBAL_10 = [3, 13, 12, 53, 0, 0, 0, 0];
const REBAL_16 = [0, 0, 0, 0, 3, 0, 0, 1];

const MARKS = [
  { t: "09-29 14:23", equity: 120.25, hodl: 120.21 },
  { t: "09-30 14:24", equity: 119.69, hodl: 119.93 },
  { t: "10-01 14:12", equity: 118.96, hodl: 119.71 },
  { t: "10-02 14:06", equity: LIVE.equity, hodl: LIVE.hodl },
];

const FACTS = [
  ["Verdict", "WATCH"],
  ["Money in", `$${CAPITAL_IN.toFixed(2)}`],
  ["Money out", `$${LIVE.equity.toFixed(2)}`],
  ["vs money-in", `+$${LIVE.vsIn.toFixed(2)}`],
  ["HODL bag", `$${LIVE.hodl.toFixed(2)}`],
  ["vs HODL", `+$${LIVE.vsHodl.toFixed(2)}`],
  ["Close→open since Sep 25", String(REBALS.total)],
  ["of which today / ~16%", `${REBALS.today} / ${REBALS.width16}`],
  ["In-range %", "no clean marks"],
  ["Fees", `owed 0; ${REBALS.collectFees} CollectFeesV2; no $ split`],
  ["Current LP", `${LIVE.lp} since ${LIVE.opened}`],
];

const DECISION = [
  ["Call", "WATCH"],
  ["Spot vs limits", "Inside 0.05% and 0.5% auto-close limits"],
  ["Recycle", "Not run — LP is in range"],
  ["YAML", "width 1.0 / threshold 0.05 left unchanged"],
  ["Volume", `97 close→open; 81 at ~1.0% (last ${REBALS.lastTight}); 1 wide open today`],
  ["Open band", "16.08% since the 05:47Z Oct 2 recenter"],
  ["Ops this run", "API :8000 down; no Docker; watchdog not restarted"],
];

export default function T013MainnetCup() {
  return (
    <Stack gap={24} style={{ padding: 24, maxWidth: 980 }}>
      <Stack gap={8}>
        <H1>T013 Orca cup — money in, money out</H1>
        <Text tone="secondary">
          Run id T013_mainnet_100_width1_20260925. Pool Czfq3xZZ. Chain mark
          2026-10-02 14:06Z. Funded bag {CAPITAL_IN.toFixed(2)} USD. HODL marks
          that same 100.25 USDC + 0.16535 SOL at spot. Finals window. Reporter
          snapshots are absent, so in-range % has no clean marks. This MTM is a
          chain mark, not a trials-ledger row.
        </Text>
        <Row gap={8} style={{ flexWrap: "wrap" }}>
          <Pill tone="warning">WATCH</Pill>
          <Pill tone="success">in range</Pill>
          <Pill>97 close→open</Pill>
          <Pill>81 at ~1.0% width</Pill>
          <Pill tone="warning">open band 16.08%</Pill>
          <Pill tone="info">1 rebalance Oct 2</Pill>
        </Row>
      </Stack>

      <Grid columns={4} gap={12}>
        <Stat value={`$${CAPITAL_IN.toFixed(2)}`} label="Money in" />
        <Stat value={`$${LIVE.equity.toFixed(2)}`} label="Money out" tone="success" />
        <Stat value={`+$${LIVE.vsIn.toFixed(2)}`} label="vs money-in" tone="success" />
        <Stat value={`+$${LIVE.vsHodl.toFixed(2)}`} label="vs HODL funded bag" tone="success" />
      </Grid>

      <Callout tone="warning" title="WATCH — recentered wide, ops unseen">
        Spot ${LIVE.price.toFixed(2)} sits inside band {LIVE.band} and inside
        auto-close limits {LIVE.limits} at threshold 0.05 (also inside the 0.5
        limits {LIVE.limitsWide}). At 05:47Z the wallet closed 5nNNxiXi…,
        swapped on Jupiter (exact-out, about $122), and opened {LIVE.lp}. That
        price was inside the prior 109.45–128.49 band, so this is a managed
        recenter of the 16% book. The new LP has been quiet {LIVE.quietHours}h.
        Recycle stays off.
      </Callout>

      <Grid columns={4} gap={12}>
        <Stat value={String(REBALS.total)} label="Close→open since Sep 25" />
        <Stat value={String(REBALS.width10)} label="~1.0% width" tone="info" />
        <Stat value="n/a" label="In-range % (clean marks)" />
        <Stat value="$0" label="fee_owed on open LP" />
      </Grid>

      <Card>
        <CardHeader trailing={<Text size="small">count</Text>}>
          Close→open by day and width
        </CardHeader>
        <CardBody>
          <LineChart
            categories={DAYS}
            series={[
              { name: "~1.5% (Sep 25, pre-1.0 cut)", data: REBAL_15, tone: "neutral" },
              { name: "~1.0% T013 band", data: REBAL_10, tone: "info" },
              { name: "~16% band", data: REBAL_16, tone: "warning" },
            ]}
            height={240}
          />
          <Text size="small" tone="secondary" style={{ marginTop: 8 }}>
            Successful Orca OpenPositionWithTokenExtensions on wallet 2ZuShDjg…,
            counted from the Oct 1 full recount plus the three wallet
            transactions on 2026-10-02. Width is (tick upper − tick lower) ×
            0.01. {REBALS.failedOpens} failed opens are excluded.{" "}
            {REBALS.collectFees} CollectFeesV2 land inside closes; principal and
            fees are not split into dollars. Oct 2 is one ~16.08% open
            (kafvBurF…), after close 4vZLgk6S… and Jupiter swap MCnZ2KRh….
          </Text>
        </CardBody>
      </Card>

      <Card>
        <CardHeader trailing={<Text size="small">USD</Text>}>
          Chain marks vs HODL
        </CardHeader>
        <CardBody>
          <LineChart
            categories={MARKS.map((p) => p.t)}
            series={[
              { name: "Strategy (money out)", data: MARKS.map((p) => p.equity), tone: "info" },
              { name: "HODL funded bag", data: MARKS.map((p) => p.hodl), tone: "neutral" },
            ]}
            referenceLines={[{ value: CAPITAL_IN, label: "Money in $119.56", tone: "warning" }]}
            beginAtZero={false}
            height={220}
          />
          <Text size="small" tone="secondary" style={{ marginTop: 8 }}>
            Earlier points are prior chain reads. Oct 2 is this read. Wallet +
            LP + position-rent marks at the pool sqrt price. The book holds more
            SOL than the funded bag, so a spot rally lifts money-out more than
            HODL. Reporter snapshots and a trials-ledger row are separate.
          </Text>
        </CardBody>
      </Card>

      <Grid columns={2} gap={16}>
        <Card>
          <CardHeader>This mark</CardHeader>
          <CardBody>
            <Table headers={["Metric", "Value"]} rows={FACTS} />
          </CardBody>
        </Card>
        <Card>
          <CardHeader>Cup call</CardHeader>
          <CardBody>
            <Table headers={["Item", "Choice"]} rows={DECISION} />
          </CardBody>
        </Card>
      </Grid>

      <Divider />

      <Stack gap={6}>
        <H2>Capital now</H2>
        <Text>
          Free {LIVE.freeSol} SOL + ${LIVE.freeUsdc.toFixed(2)} USDC. LP{" "}
          {LIVE.lpSol.toFixed(4)} SOL + ${LIVE.lpUsdc.toFixed(2)} USDC. Position
          rent {LIVE.rentSol} SOL. Pending fee_owed 0. Ticks −21876/−20268,
          liquidity 3497446047.
        </Text>
        <Text size="small" tone="secondary">
          Chain mark only. Ledger row T013 remains SUPERSEDED. Orca SOL-USDC
          Czfq3xZZ. YAML width and threshold were not edited.
        </Text>
      </Stack>
    </Stack>
  );
}
