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

/** Chain read 2026-10-06 14:13Z. Not a ledger trial row. */
const LIVE = {
  asOf: "2026-10-06 14:13Z",
  equity: 159.2,
  vsIn: 39.64,
  vsBasis: 1.64,
  hodl: 120.23,
  vsHodlPlus: 0.97,
  exTransfer: 121.2,
  price: 120.86,
  tick: -21133,
  walletSol: 0.130022084,
  walletUsdc: 26.814399,
  lpSol: 0.428566,
  lpUsdc: 63.861835,
  openAgeH: 9.4,
  flatBeforeH: 84.6,
};

/**
 * Daily public-RPC marks. The 10-06 point includes the $38 inbound USDC.
 * Reporter snapshots are absent, so this is not an hourly clean-mark series.
 */
const CHAIN_READS = [
  { t: "09-30", equity: 119.69, hodl: 119.93 },
  { t: "10-01", equity: 118.96, hodl: 119.71 },
  { t: "10-02", equity: 121.83, hodl: 120.48 },
  { t: "10-03", equity: 120.22, hodl: 119.96 },
  { t: "10-04", equity: 121.71, hodl: 120.37 },
  { t: "10-05", equity: 121.12, hodl: 120.21 },
  { t: "10-06", equity: 159.2, hodl: 120.23 },
];

const FACTS = [
  ["Verdict", "WATCH"],
  ["Current LP", "8kbPtUQx… mint 45XcrBoD… in range"],
  ["Band", "$110.59–$129.83 (1604 ticks, ~16.04%)"],
  ["Opened", "2026-10-06 04:49Z after 84.6h flat"],
  ["Spot vs limits", "$120.86 inside 0.05 and 0.5 auto-close"],
  ["n_rebals", "98 opens since Sep 25; 1 today; 0 closes today"],
  ["Last ~1.0% open", "2026-09-28 23:09Z"],
  ["In-range %", "No clean marks — snapshot dir absent"],
  ["Fees", "Pending $0; no new CollectFeesV2"],
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
          ($119.56). Money out is wallet + LP + position rent at the Orca
          SOL/USDC spot. Read {LIVE.asOf}. Pool Czfq3xZZ. Run-id
          T013_mainnet_100_width1_20260925. Chain mark only. Ledger T013 stays
          SUPERSEDED. This read is not a race P&amp;L row.
        </Text>
        <Row gap={8} style={{ flexWrap: "wrap" }}>
          <Pill tone="info">WATCH — in range</Pill>
          <Pill>~16.04% band</Pill>
          <Pill tone="warning">+$38 USDC inbound</Pill>
          <Pill>+$0.97 vs HODL after that transfer</Pill>
        </Row>
      </Stack>

      <Grid columns={4} gap={12}>
        <Stat value={`$${CAPITAL_IN}`} label="Money in (deposit mark)" />
        <Stat value={`$${LIVE.equity.toFixed(2)}`} label="Money out (wallet + LP)" />
        <Stat value={`+$${LIVE.vsBasis.toFixed(2)}`} label="vs $157.56 basis" />
        <Stat
          value={`+$${LIVE.vsHodlPlus.toFixed(2)}`}
          label="vs HODL bag + $38"
        />
      </Grid>

      <Callout tone="info" title="LP is back. The jump is a transfer.">
        Position 8kbPtUQx… opened 2026-10-06 04:49Z (tx 4A5MrzQG…) on
        Czfq3xZZ, ticks −22020/−20416, about 16.04% wide. Spot ${LIVE.price}{" "}
        (tick {LIVE.tick}) sits inside $110.59–$129.83 and inside both the
        0.05 limits ($110.54–$129.90) and the 0.5 limits ($110.04–$130.48).
        Pending fees are $0. An inbound 38 USDC arrived at 04:44Z (tx
        5D9ercnv…, memo 1791261839279249303) before a small Jupiter ExactOut
        and the open. Money out is ${LIVE.equity.toFixed(2)}. Against the
        original $119.56 that is +${LIVE.vsIn.toFixed(2)}, and $38.00 of that
        gap is the transfer. The book excluding the transfer is ${LIVE.exTransfer.toFixed(2)}{" "}
        (+$1.64 versus $119.56 and +${LIVE.vsHodlPlus.toFixed(2)} versus HODL).
        Full money out is +${LIVE.vsBasis.toFixed(2)} versus the $157.56 basis, the deposit mark
        plus the $38. Hummingbot API :8000 and gateway :15888 refused. Docker
        engine :2375 has zero containers. status returned ok:false. Watchdog
        restart and adopt --recycle were not run.
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
            ]}
            height={260}
          />
          <Text size="small" tone="secondary" style={{ marginTop: 8 }}>
            Seven public-RPC reads around 14:00Z. The 10-06 step is the $38
            USDC inbound plus the same book marked at ${LIVE.price}. The
            ex-transfer mark is ${LIVE.exTransfer.toFixed(2)}.
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
              Opens since 2026-09-25 are 98 (12×~1.5%, 81×~1.0%, 5×~16%).
              Today adds one fresh open from a flat wallet and no close.
              CollectFeesV2 stays at 97. Failed opens stay at 8. The prior
              close fee of about $0.14 is unchanged. Earlier collects still
              have no dollar total. Basis ${BASIS.toFixed(2)} = $
              {CAPITAL_IN} + ${INBOUND}.
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
          account rent 0.008408440 SOL. Pending fees $0. Spot ${LIVE.price}{" "}
          (tick {LIVE.tick}). HODL of the funded bag at this spot is $
          {LIVE.hodl.toFixed(2)}. Age of this LP is ~{LIVE.openAgeH}h. The
          wallet was flat ~{LIVE.flatBeforeH}h before the open.
        </Text>
        <Text size="small" tone="secondary">
          The live band is the ~16% shape. Repo YAML width 1.0 and threshold
          0.05 were not edited. Last ~1.0% open remains 2026-09-28 23:09Z.
        </Text>
      </Stack>
    </Stack>
  );
}
