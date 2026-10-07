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

/** Funded 100.25 USDC + 0.16535 SOL at the $116.77 deposit mark. */
const CAPITAL_IN = 119.56;
/** Inbound USDC at 2026-10-06 04:44Z. A transfer, not a fee. */
const INBOUND = 38;
const BASIS = CAPITAL_IN + INBOUND;

/** Chain read 2026-10-07 14:08Z. Not a ledger trial row. */
const LIVE = {
  asOf: "2026-10-07 14:08Z",
  equity: 156.34,
  vsIn: 36.78,
  vsBasis: -1.22,
  hodl: 119.44,
  hodlPlus: 157.44,
  vsHodlPlus: -1.1,
  exTransfer: 118.34,
  price: 116.07,
  tick: -21537,
  walletSol: 0.135695101,
  walletUsdc: 26.246069,
  lpSol: 0.612179,
  lpUsdc: 42.170347,
  rentSol: 0.00840336,
  pendingFees: 0.14,
  openAgeH: 12.1,
  flatGapH: 8.7,
};

/**
 * Daily public-RPC marks. From 10-06 the strategy series includes the $38
 * inbound USDC. Reporter snapshots are absent, so this is not an hourly
 * clean-mark series.
 */
const CHAIN_READS = [
  { t: "09-30", equity: 119.69, hodl: 119.93 },
  { t: "10-01", equity: 118.96, hodl: 119.71 },
  { t: "10-02", equity: 121.83, hodl: 120.48 },
  { t: "10-03", equity: 120.22, hodl: 119.96 },
  { t: "10-04", equity: 121.71, hodl: 120.37 },
  { t: "10-05", equity: 121.12, hodl: 120.21 },
  { t: "10-06", equity: 159.2, hodl: 120.23 },
  { t: "10-07", equity: 156.34, hodl: 119.44 },
];

const FACTS = [
  ["Verdict", "WATCH"],
  ["Current LP", "VXfubiuy… mint FDVsU8MV… in range"],
  ["Band", "$109.36–$128.44 (1608 ticks, ~16.08%)"],
  ["Opened", "2026-10-07 02:00Z after 8.7h flat"],
  ["Spot vs limits", "$116.07 inside 0.05 and 0.5 auto-close"],
  ["n_rebals", "99 opens since Sep 25; 1 close + 1 open since prior read"],
  ["Last ~1.0% open", "2026-09-28 23:09Z"],
  ["In-range %", "No clean marks — snapshot dir absent"],
  ["Fees", "Pending ~$0.14; CollectFeesV2 now 98"],
  ["This run", "status ok:false — API :8000 and gateway :15888 refused"],
];

const DECISION = [
  ["Lane", "Cup volume push — slots full, so rebalance count matters"],
  ["State", "One in-range LP on Czfq3xZZ"],
  ["Past-limit recycle", "Not indicated — spot is inside both limit bands"],
  ["What this VM did", "Left the LP open. Did not restart the watchdog"],
  ["YAML", "Leave width 1.0 and threshold 0.05 unchanged"],
  ["Ledger", "T013 row stays SUPERSEDED — this canvas is a chain mark"],
];

export default function T013MainnetCup() {
  return (
    <Stack gap={24} style={{ padding: 24, maxWidth: 980 }}>
      <Stack gap={8}>
        <H1>T013 cup — money in to money out</H1>
        <Text tone="secondary">
          Money in is 100.25 USDC + 0.16535 SOL at the $116.77 deposit mark
          ($119.56). Money out is wallet + LP + position rent + pending fees
          at the Orca SOL/USDC spot. Read {LIVE.asOf}. Pool Czfq3xZZ. Run-id
          T013_mainnet_100_width1_20260925. Chain mark only. Ledger T013 stays
          SUPERSEDED. This read is not a race PnL row.
        </Text>
        <Row gap={8} style={{ flexWrap: "wrap" }}>
          <Pill tone="info">WATCH — in range</Pill>
          <Pill>~16.08% band</Pill>
          <Pill tone="warning">8.7h flat, then reopen</Pill>
          <Pill>−$1.10 vs HODL after the $38 transfer</Pill>
        </Row>
      </Stack>

      <Grid columns={4} gap={12}>
        <Stat value={`$${CAPITAL_IN}`} label="Money in (deposit mark)" />
        <Stat value={`$${LIVE.equity.toFixed(2)}`} label="Money out (wallet + LP + fees)" />
        <Stat value={`−$${Math.abs(LIVE.vsBasis).toFixed(2)}`} label="vs $157.56 basis" />
        <Stat
          value={`−$${Math.abs(LIVE.vsHodlPlus).toFixed(2)}`}
          label="vs HODL bag + $38"
        />
      </Grid>

      <Callout tone="warning" title="In range after an 8.7h flat gap">
        Position VXfubiuy… opened 2026-10-07 02:00Z (tx NBLhbBFp…) on
        Czfq3xZZ, ticks −22132/−20524, about 16.08% wide. Spot ${LIVE.price}{" "}
        (tick {LIVE.tick}) sits inside $109.36–$128.44 and inside both the
        0.05 limits ($109.31–$128.50) and the 0.5 limits ($108.82–$129.08).
        Pending fees are ~${LIVE.pendingFees.toFixed(2)} (0.000641 SOL +
        0.06893 USDC). The prior LP 8kbPtUQx… closed 2026-10-06 17:16Z (tx
        363zDnv3…, CollectFeesV2) at an implied spot near $120.28, inside that
        band and inside both limit sets. A Jupiter ExactOut at 02:00:20Z
        (−0.953 USDC) preceded the open. Money out is ${LIVE.equity.toFixed(2)}.
        Against the original $119.56 that is +${LIVE.vsIn.toFixed(2)}, and
        $38.00 of that gap is the Oct 6 transfer. The book excluding the
        transfer is ${LIVE.exTransfer.toFixed(2)}. Full money out sits {"$" + Math.abs(LIVE.vsBasis).toFixed(2)} under the $157.56 basis. Hummingbot
        API :8000 and gateway :15888 refused. Docker engine :2375 has zero
        containers. status returned ok:false. Watchdog restart and adopt
        --recycle were not run.
      </Callout>

      <Card>
        <CardHeader trailing={<Text size="small">USD</Text>}>
          Strategy mark vs HODL funded bag
        </CardHeader>
        <CardBody>
          <LineChart
            categories={CHAIN_READS.map((p) => p.t)}
            series={[
              {
                name: "Strategy (chain mark)",
                data: CHAIN_READS.map((p) => p.equity),
                tone: "info",
              },
              {
                name: "HODL 100.25 USDC + 0.16535 SOL",
                data: CHAIN_READS.map((p) => p.hodl),
                tone: "neutral",
              },
            ]}
            referenceLines={[
              {
                value: CAPITAL_IN,
                label: "Money in $119.56",
                tone: "warning",
              },
              {
                value: BASIS,
                label: "Basis $157.56",
                tone: "info",
              },
            ]}
            height={260}
          />
          <Text size="small" tone="secondary" style={{ marginTop: 8 }}>
            Eight public-RPC reads around 14:00Z. The 10-06 step is the $38
            USDC inbound. The 10-07 mark is ${LIVE.equity.toFixed(2)} at spot $
            {LIVE.price}, including ~${LIVE.pendingFees.toFixed(2)} of pending
            fees. The ex-transfer mark is ${LIVE.exTransfer.toFixed(2)}.
            data/devnet_runs/T013_mainnet_100_width1_20260925 is absent, so
            there is no clean hourly in-range series.
          </Text>
        </CardBody>
      </Card>

      <Grid columns={2} gap={16}>
        <Card>
          <CardHeader>Book and volume</CardHeader>
          <CardBody>
            <Table headers={["Metric", "Value"]} rows={FACTS} />
          </CardBody>
        </Card>
        <Card>
          <CardHeader>Decision</CardHeader>
          <CardBody>
            <Table headers={["Item", "Choice"]} rows={DECISION} />
            <Text size="small" tone="secondary" style={{ marginTop: 8 }}>
              Opens since 2026-09-25 are 99 (12×~1.5%, 81×~1.0%, 6×~16%).
              Since the prior read: one in-range close and one fresh open.
              CollectFeesV2 is 98. Failed opens stay at 8. The close and the
              open are still one ~16% recenter, and the last ~1.0% open remains
              2026-09-28 23:09Z. Basis ${BASIS.toFixed(2)} = ${CAPITAL_IN} + $
              {INBOUND}.
            </Text>
          </CardBody>
        </Card>
      </Grid>

      <Divider />

      <Stack gap={6}>
        <H2>Capital now</H2>
        <Text>
          Wallet {LIVE.walletSol} SOL + ${LIVE.walletUsdc} USDC. LP{" "}
          {LIVE.lpSol} SOL + ${LIVE.lpUsdc} USDC. Position, mint, and NFT
          account rent {LIVE.rentSol} SOL. Pending fees ~$
          {LIVE.pendingFees.toFixed(2)}. Spot ${LIVE.price} (tick {LIVE.tick}).
          HODL of the funded bag at this spot is ${LIVE.hodl.toFixed(2)}. HODL
          plus the $38 transfer is ${LIVE.hodlPlus.toFixed(2)}. Age of this LP
          is ~{LIVE.openAgeH}h. The wallet was flat ~{LIVE.flatGapH}h between
          the close and this open.
        </Text>
        <Text size="small" tone="secondary">
          The live band is the ~16% shape. Repo YAML width 1.0 and threshold
          0.05 were not edited. Last ~1.0% open remains 2026-09-28 23:09Z.
          Spot fell from $120.86 to $116.07 while the book holds more SOL than
          the 0.16535 deposit, so the mark fell further than HODL.
        </Text>
      </Stack>
    </Stack>
  );
}
