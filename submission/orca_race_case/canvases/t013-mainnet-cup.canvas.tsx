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

/** Chain mark 2026-09-30 14:24Z. Includes position-NFT rent. Not a ledger row. */
const LIVE = {
  equity: 119.69,
  vsIn: 0.13,
  vsHodl: -0.24,
  hodl: 119.93,
  price: 119.01,
  inRange: true,
  widthPct: 16.06,
  lp: "5nNNxiXi…",
  band: "[109.45, 128.49]",
  limits: "[109.40, 128.56]",
  freeSol: 0.1234,
  freeUsdc: 7.77,
  lpSol: 0.387,
  lpUsdc: 50.21,
  rentSol: 0.00841,
  opened: "2026-09-29 20:25Z",
  quietHours: 18.0,
};

const REBALS = {
  total: 96,
  width15: 12,
  width10: 81,
  width16: 3,
  failedOpens: 8,
  collectFees: 95,
  lastTight: "2026-09-28 23:09Z",
};

const DAYS = ["Sep 25", "Sep 26", "Sep 27", "Sep 28", "Sep 29", "Sep 30"];
const REBAL_15 = [12, 0, 0, 0, 0, 0];
const REBAL_10 = [3, 13, 12, 53, 0, 0];
const REBAL_16 = [0, 0, 0, 0, 3, 0];

const MARKS = [
  { t: "09-29 14:23", equity: 120.25, hodl: 120.21 },
  { t: "09-30 14:24", equity: LIVE.equity, hodl: LIVE.hodl },
];

const FACTS = [
  ["Verdict", "WATCH"],
  ["Money in", `$${CAPITAL_IN.toFixed(2)}`],
  ["Money out", `$${LIVE.equity.toFixed(2)}`],
  ["vs money-in", `+$${LIVE.vsIn.toFixed(2)}`],
  ["HODL bag", `$${LIVE.hodl.toFixed(2)}`],
  ["vs HODL", `−$${Math.abs(LIVE.vsHodl).toFixed(2)}`],
  ["Close→open since Sep 25", String(REBALS.total)],
  ["of which ~1.0% width", String(REBALS.width10)],
  ["In-range %", "no clean marks"],
  ["Fees", `owed 0; ${REBALS.collectFees} CollectFeesV2; no $ split`],
  ["Current LP", `${LIVE.lp} since ${LIVE.opened}`],
];

const DECISION = [
  ["Call", "WATCH"],
  ["Spot vs limits", "Inside 0.05% auto-close limits"],
  ["Recycle", "Not run — LP is in range"],
  ["YAML", "width 1.0 / threshold 0.05 left unchanged"],
  ["Volume", `81 tight closes→opens; last one ${REBALS.lastTight}`],
  ["Open band", "16.06% since the 20:25Z Sep 29 recenter"],
  ["Ops this run", "Docker and :8000 unreachable; watchdog not restarted"],
];

export default function T013MainnetCup() {
  return (
    <Stack gap={24} style={{ padding: 24, maxWidth: 980 }}>
      <Stack gap={8}>
        <H1>T013 Orca cup — money in, money out</H1>
        <Text tone="secondary">
          Run id T013_mainnet_100_width1_20260925. Pool Czfq3xZZ. Chain mark
          2026-09-30 14:24Z. Funded bag {CAPITAL_IN.toFixed(2)} USD. HODL marks
          that same 100.25 USDC + 0.16535 SOL at spot. Reporter snapshots are
          absent on this machine, so in-range % has no clean marks.
        </Text>
        <Row gap={8} style={{ flexWrap: "wrap" }}>
          <Pill tone="warning">WATCH</Pill>
          <Pill tone="success">in range</Pill>
          <Pill>96 close→open</Pill>
          <Pill>81 at ~1.0% width</Pill>
          <Pill tone="warning">open band 16.1%</Pill>
        </Row>
      </Stack>

      <Grid columns={4} gap={12}>
        <Stat value={`$${CAPITAL_IN.toFixed(2)}`} label="Money in" />
        <Stat value={`$${LIVE.equity.toFixed(2)}`} label="Money out" />
        <Stat value={`+$${LIVE.vsIn.toFixed(2)}`} label="vs money-in" tone="success" />
        <Stat
          value={`−$${Math.abs(LIVE.vsHodl).toFixed(2)}`}
          label="vs HODL funded bag"
          tone="warning"
        />
      </Grid>

      <Callout tone="warning" title="WATCH — in range, tight-band volume idle">
        Spot ${LIVE.price.toFixed(2)} sits inside band {LIVE.band} and inside
        auto-close limits {LIVE.limits} (threshold 0.05). LP {LIVE.lp} has been
        open {LIVE.quietHours.toFixed(1)}h with no later wallet transaction.
        Recycle stays off. The 1.0% close→open streak ended {REBALS.lastTight}.
        The live position is a 16.06% band.
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
            Successful Orca OpenPositionWithTokenExtensions after a successful
            close, wallet 2ZuShDjg…. Sep 30 is through 14:24Z. {REBALS.failedOpens}{" "}
            failed opens are excluded. {REBALS.collectFees} CollectFeesV2 land
            inside closes; principal and fees are not split into dollars.
          </Text>
        </CardBody>
      </Card>

      <Card>
        <CardHeader trailing={<Text size="small">USD</Text>}>
          Two chain marks vs HODL
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
            Sep 29 point is the prior chain read (LP Ee7c…, spot $120.71). Sep 30
            point is this read. These are wallet + LP + position-rent marks, not
            reporter snapshots and not a trials-ledger row.
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
          {LIVE.lpSol} SOL + ${LIVE.lpUsdc.toFixed(2)} USDC. Position rent{" "}
          {LIVE.rentSol} SOL. Pending fee_owed 0.
        </Text>
        <Text size="small" tone="secondary">
          Chain mark only. Ledger row T013 remains SUPERSEDED. Orca SOL-USDC
          Czfq3xZZ. YAML width and threshold were not edited.
        </Text>
      </Stack>
    </Stack>
  );
}
