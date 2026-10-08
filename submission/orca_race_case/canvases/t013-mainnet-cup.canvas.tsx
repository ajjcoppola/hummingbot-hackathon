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

/** Deposit-day money-in: 100.25 USDC + 0.16535 SOL at $116.77. */
const CAPITAL_IN = 119.56;
/** Same bag plus the 2026-10-06 inbound 38 USDC (tx 5D9ercnv…). */
const BASIS = 157.56;
const TRANSFER_IN = 38;

const LIVE = {
  ts: "2026-10-08T14:11:13Z",
  price: 112.45,
  tick: -21854,
  equity: 153.46,
  exTransfer: 115.46,
  vsIn: 33.9,
  vsBasis: -4.1,
  hodl: 118.84,
  hodl38: 156.84,
  vsHodl38: -3.39,
  inRange: true,
  lp: "VXfubiuy…",
  mint: "FDVsU8MV…",
  band: "[109.36, 128.44]",
  logWidth: 16.08,
  ageH: 36.2,
  walletSol: 0.135695101,
  walletUsdc: 26.246069,
  lpSol: 0.8099,
  lpUsdc: 19.5815,
  rentSol: 0.00840336,
  feeSol: 0.001603,
  feeUsdc: 0.1715,
  feeUsd: 0.35,
  opens: 99,
  opensToday: 0,
};

/**
 * Morning chain marks. Ex-transfer subtracts the $38 inbound from Oct 6 on,
 * so the line stays comparable to the original funded bag.
 * These are not reporter snapshots.
 */
const MARKS = [
  { t: "09-30", ex: 119.69, hodl: 119.93 },
  { t: "10-01", ex: 118.96, hodl: 119.71 },
  { t: "10-02", ex: 121.83, hodl: 120.48 },
  { t: "10-03", ex: 120.22, hodl: 119.96 },
  { t: "10-04", ex: 121.71, hodl: 120.37 },
  { t: "10-05", ex: 121.12, hodl: 120.21 },
  { t: "10-06", ex: 121.2, hodl: 120.23 },
  { t: "10-07", ex: 118.34, hodl: 119.44 },
  { t: "10-08", ex: 115.46, hodl: 118.84 },
];

const FACTS = [
  ["Read", "2026-10-08 14:11Z public RPC"],
  ["Current LP", "VXfubiuy… in range, age 36.2h"],
  ["Band", "$109.36–$128.44 (16.08% log-width)"],
  ["Spot vs limits", "$112.45 inside 0.05 and 0.5"],
  ["Opens since Sep 25", "99 (0 since the Oct 7 02:00Z open)"],
  ["Last ~1.0% open", "2026-09-28 23:09Z"],
  ["In-range %", "no clean marks (snapshot dir absent)"],
  ["Pending fees", "0.001603 SOL + 0.1715 USDC ≈ $0.35"],
  ["Wallet tx since open", "none"],
];

const DECISION = [
  ["Verdict", "WATCH"],
  ["Recycle", "Not run. Spot is inside both auto-close limits."],
  ["YAML", "Width and threshold unchanged."],
  ["Volume", "0 new close→open in 36.2h. Live band is ~16%, not 1.0%."],
  ["Ledger", "T013 stays SUPERSEDED. This is a chain mark."],
  ["Ops", "API :8000 refused. Watchdog not started on this VM."],
];

export default function T013MainnetCup() {
  return (
    <Stack gap={24} style={{ padding: 24, maxWidth: 980 }}>
      <Stack gap={8}>
        <H1>T013 cup — money in, money out</H1>
        <Text tone="secondary">
          Pool Czfq3xZZ. Money-in ${CAPITAL_IN} = 100.25 USDC + 0.16535 SOL at
          the $116.77 deposit mark. Chain read {LIVE.ts}. Marks are wallet + LP
          + position rent + pending fees. HODL is that same funded bag at spot.
          The $38 USDC inbound on 2026-10-06 is a transfer, not fees.
        </Text>
        <Row gap={8} style={{ flexWrap: "wrap" }}>
          <Pill tone="warning">WATCH</Pill>
          <Pill tone="success">in range</Pill>
          <Pill tone="info">0 new rebals / 36.2h</Pill>
          <Pill>99 opens since Sep 25</Pill>
        </Row>
      </Stack>

      <Grid columns={4} gap={12}>
        <Stat value={`$${CAPITAL_IN}`} label="Money in (deposit mark)" />
        <Stat value={`$${LIVE.equity.toFixed(2)}`} label="Money out (chain mark)" />
        <Stat
          value={`−$${Math.abs(LIVE.vsBasis).toFixed(2)}`}
          label="vs $157.56 basis (in + $38)"
          tone="warning"
        />
        <Stat
          value={`−$${Math.abs(LIVE.vsHodl38).toFixed(2)}`}
          label="vs HODL funded + $38"
          tone="warning"
        />
      </Grid>

      <Callout tone="warning" title="WATCH — in range, rebalance volume stalled">
        One LP {LIVE.lp} (mint {LIVE.mint}), band {LIVE.band}, log-width{" "}
        {LIVE.logWidth}%. Spot ${LIVE.price} (tick {LIVE.tick}) is inside the
        0.05 limits ($109.31–$128.50) and the 0.5 limits ($108.82–$129.08).
        About 2.8% above the lower edge. Auto-close has not been breached, so
        adopt --recycle was not run. No wallet transaction since the open at
        2026-10-07 02:00:25Z. Last ~1.0% open is still 2026-09-28 23:09Z. Cup
        slots are full; this window added no rebalance volume. Width and
        threshold were left as they are.
      </Callout>

      <Card>
        <CardHeader trailing={<Text size="small">USD</Text>}>
          Ex-transfer mark vs HODL funded bag
        </CardHeader>
        <CardBody>
          <LineChart
            categories={MARKS.map((p) => p.t)}
            series={[
              {
                name: "Strategy ex-$38 transfer",
                data: MARKS.map((p) => p.ex),
                tone: "info",
              },
              {
                name: "HODL 100.25 USDC + 0.16535 SOL",
                data: MARKS.map((p) => p.hodl),
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
            Daily chain marks, 2026-09-30 through 2026-10-08. From Oct 6 the
            strategy line subtracts the $38 inbound so it can sit next to the
            original bag. Full money out today is ${LIVE.equity.toFixed(2)},
            which still includes that $38. Snapshot directory
            data/devnet_runs/T013_mainnet_100_width1_20260925 is absent, so
            there is no clean in-range percent.
          </Text>
        </CardBody>
      </Card>

      <Grid columns={2} gap={16}>
        <Card>
          <CardHeader>This read</CardHeader>
          <CardBody>
            <Table headers={["Metric", "Value"]} rows={FACTS} />
          </CardBody>
        </Card>
        <Card>
          <CardHeader>Decision</CardHeader>
          <CardBody>
            <Table headers={["Item", "Choice"]} rows={DECISION} />
            <Text size="small" tone="secondary" style={{ marginTop: 8 }}>
              Hummingbot API :8000 and gateway :15888 refused. Docker engine
              :2375 is up with zero containers. Reporter and watchdog were not
              started here.
            </Text>
          </CardBody>
        </Card>
      </Grid>

      <Divider />

      <Stack gap={6}>
        <H2>Capital composition</H2>
        <Text>
          Wallet {LIVE.walletSol} SOL + ${LIVE.walletUsdc} USDC. LP {LIVE.lpSol}{" "}
          SOL + ${LIVE.lpUsdc} USDC. Position rent {LIVE.rentSol} SOL. Pending
          fees {LIVE.feeSol} SOL + {LIVE.feeUsdc} USDC (≈ ${LIVE.feeUsd}).
        </Text>
        <Text size="small" tone="secondary">
          Chain mark only. Ledger row T013 remains SUPERSEDED. Ex-transfer book
          ${LIVE.exTransfer.toFixed(2)} versus HODL ${LIVE.hodl.toFixed(2)}.
          Raw money out versus the ${CAPITAL_IN} deposit is +$
          {LIVE.vsIn.toFixed(2)}, and ${TRANSFER_IN} of that gap is the Oct 6
          transfer. Versus the ${BASIS.toFixed(2)} basis the mark is −$
          {Math.abs(LIVE.vsBasis).toFixed(2)}. Opens since 2026-09-25: {LIVE.opens} (12
          near 1.5%, 81 near 1.0%, 6 near 16%). CollectFeesV2 still 98. Failed
          opens still 8.
        </Text>
      </Stack>
    </Stack>
  );
}
