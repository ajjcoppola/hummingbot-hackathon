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
  ts: "2026-10-09T14:14Z",
  price: 109.51,
  tick: -22119,
  equity: 149.72,
  exTransfer: 111.72,
  vsIn: 30.16,
  vsBasis: -7.84,
  hodl: 118.36,
  hodl38: 156.36,
  vsHodl38: -6.64,
  inRange: true,
  lp: "38qkUcFX…",
  mint: "EBGHyj7T…",
  band: "[107.76, 125.04]",
  priceRatio: 16.04,
  logWidth: 14.88,
  ageH: 21.3,
  idleH: 12.2,
  walletSol: 0.398878,
  walletUsdc: 74.089494,
  lpSol: 0.251193,
  lpUsdc: 3.456182,
  rentSol: 0.00840844,
  feeSol: 0.000262,
  feeUsdc: 0.029982,
  feeUsd: 0.06,
  opens: 103,
  opensBurst: 4,
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
  { t: "10-09", ex: 111.72, hodl: 118.36 },
];

const FACTS = [
  ["Read", "2026-10-09 14:14Z public RPC"],
  ["Current LP", "38qkUcFX… in range, age 21.3h"],
  ["Band", "$107.76–$125.04 (16.0% price ratio, 14.88% log)"],
  ["Spot vs limits", "$109.51 inside 0.05 and 0.5"],
  ["Opens since Sep 25", "103 (4 on Oct 8 after 14:11Z, 0 on Oct 9)"],
  ["Last ~1.0% open", "2026-09-28 23:09Z"],
  ["In-range %", "no clean marks (snapshot dir absent)"],
  ["Pending fees", "0.000262 SOL + 0.0300 USDC ≈ $0.06"],
  ["Idle quote", "large LP closed 02:00Z, no reopen (~12.2h)"],
];

const DECISION = [
  ["Verdict", "ACTION"],
  ["Recycle", "Not run. Remaining LP is inside both auto-close limits."],
  ["YAML", "Width and threshold unchanged."],
  ["Volume", "4 opens on Oct 8, then the ~16% log LP closed with no Oct 9 open."],
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
          <Pill tone="danger">ACTION</Pill>
          <Pill tone="success">remnant in range</Pill>
          <Pill tone="warning">quote idle ~{LIVE.idleH}h</Pill>
          <Pill>{LIVE.opens} opens since Sep 25</Pill>
        </Row>
      </Stack>

      <Grid columns={4} gap={12}>
        <Stat value={`$${CAPITAL_IN}`} label="Money in (deposit mark)" />
        <Stat value={`$${LIVE.equity.toFixed(2)}`} label="Money out (chain mark)" />
        <Stat
          value={`−$${Math.abs(LIVE.vsBasis).toFixed(2)}`}
          label="vs $157.56 basis (in + $38)"
          tone="danger"
        />
        <Stat
          value={`−$${Math.abs(LIVE.vsHodl38).toFixed(2)}`}
          label="vs HODL funded + $38"
          tone="warning"
        />
      </Grid>

      <Callout tone="danger" title="ACTION — large LP closed, quote not reopened">
        The ~16% log-width LP 5M8ca88… (ticks −23156/−21548) closed at
        2026-10-09 02:00:03Z (tx 3fRF6rok…, CollectFeesV2 + close). No open
        after that. About ${LIVE.walletUsdc.toFixed(2)} USDC and {LIVE.walletSol}{" "}
        SOL are free. A smaller LP {LIVE.lp} (mint {LIVE.mint}) from 2026-10-08
        16:57Z is still in range, band {LIVE.band}, about 1.6% above the lower
        price. Spot ${LIVE.price} (tick {LIVE.tick}) is inside the 0.05 limits
        ($107.70–$125.11) and the 0.5 limits ($107.22–$125.67), so adopt
        --recycle was not run. Two LPs overlapped from 17:05Z to 02:00Z. Width
        and threshold were left as they are. Last ~1.0% open is still
        2026-09-28 23:09Z.
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
            Daily chain marks, 2026-09-30 through 2026-10-09. From Oct 6 the
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
              :2375 is up with zero containers (image is buildkit only).
              Reporter and watchdog were not started here.
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
          {Math.abs(LIVE.vsBasis).toFixed(2)}. Versus HODL plus $38 the mark is
          −${Math.abs(LIVE.vsHodl38).toFixed(2)}. Opens since 2026-09-25:{" "}
          {LIVE.opens} (12 near 1.5%, 81 near 1.0%, 7 near 16% log, 3 at 1488
          ticks / ~16% price ratio). Oct 8 burst after the prior read:{" "}
          {LIVE.opensBurst} successful opens, 1 failed open (custom 6069), 4
          closes. Oct 9 opens: {LIVE.opensToday}. CollectFeesV2 now 102. Failed
          opens now 9. Close fees on the four new closes were not split from
          principal.
        </Text>
      </Stack>
    </Stack>
  );
}
