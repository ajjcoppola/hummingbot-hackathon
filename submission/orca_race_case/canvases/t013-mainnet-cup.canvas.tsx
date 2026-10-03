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

/** Chain read 2026-10-03 14:11Z. Not a ledger trial row. */
const LIVE = {
  asOf: "2026-10-03 14:11Z",
  equity: 120.22,
  vsIn: 0.66,
  hodl: 119.96,
  vsHodl: 0.27,
  price: 119.19,
  tick: -21272,
  walletSol: 0.593074,
  walletUsdc: 49.535901,
  solUsd: 70.69,
  flatHours: 22.0,
  heldHours: 10.4,
  closeFeeUsd: 0.14,
};

/**
 * Daily public-RPC marks of the same wallet. Reporter snapshots are absent,
 * so this is not an hourly clean-mark series.
 */
const CHAIN_READS = [
  { t: "09-30", equity: 119.69, hodl: 119.93 },
  { t: "10-01", equity: 118.96, hodl: 119.71 },
  { t: "10-02", equity: 121.83, hodl: 120.48 },
  { t: "10-03", equity: 120.22, hodl: 119.96 },
];

const FACTS = [
  ["Verdict", "ACTION"],
  ["Current LP", "None — flat since 2026-10-02 16:14Z"],
  ["Last LP", "78Spb3n7… mint HM9dyv6… ticks −21876/−20268"],
  ["Last band", "$112.20–$131.77 (~16.08% wide)"],
  ["Close", "In range at ~$119.98 (inside 0.05 and 0.5 limits)"],
  ["Time in that LP", "~10.4h, then ~22h with no position"],
  ["n_rebals (opens since Sep 25)", "97 carried; 0 after the Oct 2 close"],
  ["Last ~1.0% open", "2026-09-28 23:09Z"],
  ["In-range %", "No clean marks — snapshot dir absent"],
  ["Fees", "$0.14 on that close; pending $0; no cumulative $"],
  ["This run", "API :8000 and gateway :15888 refused; Docker absent"],
];

const DECISION = [
  ["Lane", "Cup volume push — slots full, so rebalance count matters"],
  ["State", "Capital is in the wallet, not in Whirlpool"],
  ["Past-limit recycle", "Not indicated — no open LP, and the close was in range"],
  ["What the Mac should do", "Confirm the bot, then hard-restart only if the cup LP should be live"],
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
          ($119.56). Money out is the wallet marked at the Orca SOL/USDC spot.
          Read {LIVE.asOf}. Pool Czfq3xZZ. Run-id
          T013_mainnet_100_width1_20260925. Chain mark only — ledger T013 is
          SUPERSEDED and this is not a race P&amp;L row.
        </Text>
        <Row gap={8} style={{ flexWrap: "wrap" }}>
          <Pill tone="warning">ACTION — flat ~{LIVE.flatHours}h</Pill>
          <Pill tone="warning">No LP</Pill>
          <Pill tone="info">+$0.66 vs money-in</Pill>
          <Pill>+$0.27 vs HODL</Pill>
        </Row>
      </Stack>

      <Grid columns={4} gap={12}>
        <Stat value={`$${CAPITAL_IN}`} label="Money in (deposit mark)" />
        <Stat value={`$${LIVE.equity}`} label="Money out (wallet now)" />
        <Stat value={`+$${LIVE.vsIn.toFixed(2)}`} label="vs money-in" tone="success" />
        <Stat value={`+$${LIVE.vsHodl.toFixed(2)}`} label="vs HODL funded bag" />
      </Grid>

      <Callout tone="warning" title="Flat after an in-range close">
        Position 78Spb3n7… closed 2026-10-02 16:14Z (tx 5Mw8jFF5…) while spot
        was about $119.98, inside the $112.20–$131.77 band and inside both the
        0.05 and 0.5 auto-close limits. No later open. Wallet now holds{" "}
        {LIVE.walletSol} SOL and {LIVE.walletUsdc} USDC. This VM cannot see
        Docker, Hummingbot API :8000, or gateway :15888, so status, watchdog
        restart, and adopt --recycle were not run. Recycle is the stranded-LP
        path; there is no open LP to recycle.
      </Callout>

      <Card>
        <CardHeader trailing={<Text size="small">USD</Text>}>
          Strategy wallet vs HODL funded bag
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
            Four public-RPC reads around 14:00Z. data/devnet_runs/
            T013_mainnet_100_width1_20260925 is absent, so there is no clean
            hourly in-range series.
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
              Opens since 2026-09-25 stay at 97 (12×~1.5%, 81×~1.0%, 4×~16%),
              carried from the 2026-10-02 signature walk and confirmed by no
              newer open. Oct 3 adds one CollectFeesV2 on the close
              (0.000601 SOL + 0.069622 USDC ≈ ${LIVE.closeFeeUsd} at ~$119.98)
              and no dollar total for earlier collects.
            </Text>
          </CardBody>
        </Card>
      </Grid>

      <Divider />

      <Stack gap={6}>
        <H2>Capital now</H2>
        <Text>
          Wallet {LIVE.walletSol} SOL (${LIVE.solUsd}) + ${LIVE.walletUsdc}{" "}
          USDC. LP $0. Pending fees $0. Spot ${LIVE.price} (tick {LIVE.tick}).
          HODL of the funded bag at this spot is ${LIVE.hodl}.
        </Text>
        <Text size="small" tone="secondary">
          Last on-chain band was the ~16% recenter, wider than the T013 YAML
          width of 1.0%. Threshold and width files were not edited.
        </Text>
      </Stack>
    </Stack>
  );
}
