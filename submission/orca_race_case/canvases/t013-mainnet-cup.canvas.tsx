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
  ts: "2026-10-10T14:06Z",
  price: 109.77,
  tick: -22095,
  equity: 149.91,
  exTransfer: 111.91,
  vsIn: 30.35,
  vsBasis: -7.65,
  hodl: 118.4,
  hodl38: 156.4,
  vsHodl38: -6.49,
  inRange: false,
  lp: "none",
  closedLp: "38qkUcFX…",
  band: "[107.76, 125.04]",
  closePrice: 110.24,
  flatH: 8.4,
  heldH: 36.8,
  walletSol: 0.6459383,
  walletUsdc: 79.009155,
  feeSol: 0.000387825,
  feeUsdc: 0.044227,
  feeUsd: 0.09,
  opens: 103,
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
  { t: "10-10", ex: 111.91, hodl: 118.4 },
];

const FACTS = [
  ["Money in", "$119.56 (100.25 USDC + 0.16535 SOL @ $116.77)"],
  ["Money out", "$149.91 chain mark (wallet only)"],
  ["vs HODL", "−$6.49 vs funded bag + $38 ($156.40)"],
  ["n_rebals", "103 successful opens since Sep 25; 0 on Oct 10"],
  ["In-range %", "no clean marks (snapshot dir absent)"],
  ["Fees", "this close 0.000388 SOL + 0.0442 USDC ≈ $0.09; pending $0"],
  ["Current LP", "none — 38qkUcFX… closed in range 05:42Z"],
  ["Verdict", "ACTION"],
];

const DECISION = [
  ["Verdict", "ACTION"],
  ["Recycle", "Not run. Close was inside 0.05 and 0.5 limits; no LP left."],
  ["YAML", "Width and threshold unchanged."],
  ["Volume", "0 opens on Oct 10. Last ~1.0% open still 2026-09-28 23:09Z."],
  ["Ledger", "T013 stays SUPERSEDED. This is a chain mark."],
  ["Ops", "status ok:false. API refused. Watchdog not started here."],
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
          <Pill tone="warning">flat ~{LIVE.flatH}h</Pill>
          <Pill>no open LP</Pill>
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

      <Callout tone="danger" title="ACTION — in-range close, quote not reopened">
        LP {LIVE.closedLp} (mint EBGHyj7T…, ticks −22280/−20792) closed at
        2026-10-10 05:42:17Z (tx 9Z3om8uz…, CollectFeesV2 + close). Implied spot
        at the close was about ${LIVE.closePrice}, inside the band {LIVE.band}{" "}
        and inside both the 0.05 limits ($107.70–$125.11) and the 0.5 limits
        ($107.22–$125.67). No open followed. Wallet is flat: {LIVE.walletSol}{" "}
        SOL + ${LIVE.walletUsdc} USDC, idle ~{LIVE.flatH}h. Spot now $
        {LIVE.price} (tick {LIVE.tick}) would still sit inside that old band, so
        this is not a past-limit strand and adopt --recycle was not run. The
        position had been open ~{LIVE.heldH}h. Width and threshold were left as
        they are. Last ~1.0% open is still 2026-09-28 23:09Z. Oct 10 opens:{" "}
        {LIVE.opensToday}.
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
            Daily chain marks, 2026-09-30 through 2026-10-10. From Oct 6 the
            strategy line subtracts the $38 inbound so it can sit next to the
            original bag. Full money out today is ${LIVE.equity.toFixed(2)},
            which still includes that $38. Snapshot directory
            data/devnet_runs/T013_mainnet_100_width1_20260925 is absent, so
            there is no clean in-range percent and no reporter n_rebals.
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
              Hummingbot API :8000 and gateway :15888 refused
              (mainnet_bot_ops.py status ok:false at 14:06Z). Docker engine
              :2375 is up with zero containers (image is buildkit only). No
              reporter or watchdog process. MAINNET_OPS.md has no nohup start;
              LaunchAgents are the Mac path, so the watchdog was not started
              on this VM.
            </Text>
          </CardBody>
        </Card>
      </Grid>

      <Divider />

      <Stack gap={6}>
        <H2>Capital composition</H2>
        <Text>
          Wallet {LIVE.walletSol} SOL + ${LIVE.walletUsdc} USDC. No LP, no
          position rent left out, pending fees $0. This close returned
          principal 0.238276 SOL + 4.875434 USDC and fees {LIVE.feeSol} SOL +{" "}
          {LIVE.feeUsdc} USDC (≈ ${LIVE.feeUsd} at the current mark). Rent
          0.008408440 SOL came back to the wallet. Network fee on the close was
          0.000011618 SOL.
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
          ticks / ~16% price ratio). Oct 10 opens: {LIVE.opensToday}.
          CollectFeesV2 now 103. Failed opens still 9. A later signature,
          4CqwxugJ… at 05:42:28Z, moved 1 lamport from 7xsxyfNR… into this
          wallet among many others. It is not a deposit and not a fee. Cup
          rebalance volume did not increase today.
        </Text>
      </Stack>
    </Stack>
  );
}
