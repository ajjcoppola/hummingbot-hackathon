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

/** Deposit mark: 100.25 USDC + 0.16535 SOL at $116.77. Not a ledger trial row. */
const MONEY_IN = 119.56;
/** Original deposit plus the 2026-10-06 +38 USDC inbound (tx 5D9ercnv…). */
const BASIS = 157.56;

const LIVE = {
  ts: "2026-10-11T14:03:03Z",
  spot: 109.324,
  tickPrice: 109.319,
  tick: -22136,
  moneyOut: 149.63,
  vsIn: 30.07,
  vsBasis: -7.93,
  hodlFunded: 118.33,
  hodlFair: 156.33,
  vsHodlFair: -6.7,
  exTransfer: 111.63,
  vsPrior: -0.28,
  sol: 0.6459383,
  usdc: 79.009155,
  flatHours: 32.3,
  opens: 103,
  cupWindowOpens: 5,
  pendingFees: 0,
};

/**
 * Daily chain marks. Fair HODL is the funded bag, plus $38 cash from Oct 6.
 * Both lines step up that day because of the inbound transfer, not fees.
 */
const DAILY = [
  { t: "09-30", equity: 119.69, hodl: 119.93 },
  { t: "10-01", equity: 118.96, hodl: 119.71 },
  { t: "10-02", equity: 121.83, hodl: 120.48 },
  { t: "10-03", equity: 120.22, hodl: 119.96 },
  { t: "10-04", equity: 121.71, hodl: 120.37 },
  { t: "10-05", equity: 121.12, hodl: 120.21 },
  { t: "10-06", equity: 159.2, hodl: 158.23 },
  { t: "10-07", equity: 156.34, hodl: 157.44 },
  { t: "10-08", equity: 153.46, hodl: 156.84 },
  { t: "10-09", equity: 149.72, hodl: 156.36 },
  { t: "10-10", equity: 149.91, hodl: 156.4 },
  { t: "10-11", equity: 149.63, hodl: 156.33 },
];

const SCORE = [
  ["Money in", "$119.56 (100.25 USDC + 0.16535 SOL @ $116.77)"],
  ["Money out", "$149.63 wallet only"],
  ["vs money-in", "+$30.07, of which $38.00 is the Oct 6 inbound"],
  ["vs basis $157.56", "−$7.93"],
  ["vs HODL (funded + $38)", "−$6.70"],
  ["Ex-transfer book", "$111.63"],
  ["n_rebals", "Reporter n/a. Chain opens since Sep 25: 103. Opens since Oct 10 05:42Z: 0"],
  ["In-range %", "No clean marks. Snapshot dir absent"],
  ["Fees", "Pending $0. Last close collected ~$0.09 (Oct 10). No cumulative trial-row fee sum"],
  ["Current LP", "None. Token-2022 accounts: 0"],
  ["Verdict", "ACTION"],
];

const VOLUME = [
  ["Since 2026-09-25", "103 successful opens"],
  ["Width mix", "12× ~1.5%, 81× ~1.0%, 7× ~16.08% log, 3× 1488-tick"],
  ["Last ~1.0% open", "2026-09-28 23:09Z"],
  ["Cup window Oct 7 02:00Z–Oct 9 02:00Z", "5 opens, all ~16% wide"],
  ["Since close 2026-10-10 05:42Z", "0 opens, flat ~32.3h"],
  ["CollectFeesV2 / failed opens", "103 / 9, unchanged today"],
];

const OPS = [
  ["Status 14:03Z", "ok: false. API :8000 and gateway :15888 refused"],
  ["Docker :2375", "Engine up, 0 containers, image moby/buildkit only"],
  ["Reporter / watchdog", "No process on this VM. Not started"],
  ["Recycle", "Not run. No open LP to strand past auto-close limits"],
  ["YAML", "Width 1.0% and threshold 0.05 unchanged"],
];

export default function T013MainnetCup() {
  return (
    <Stack gap={24} style={{ padding: 24, maxWidth: 980 }}>
      <Stack gap={8}>
        <H1>T013 mainnet — money in, money out</H1>
        <Text tone="secondary">
          Chain mark at {LIVE.ts}. Pool Czfq3xZZ SOL-USDC. Spot ${LIVE.spot}{" "}
          (sqrt; tick price ${LIVE.tickPrice}, tick {LIVE.tick}). Wallet{" "}
          {LIVE.sol} SOL + {LIVE.usdc} USDC. Same balances as the Oct 10 close.
          This is a chain mark, not a ledger trial row. T013 stays SUPERSEDED.
        </Text>
        <Row gap={8} style={{ flexWrap: "wrap" }}>
          <Pill tone="warning">ACTION</Pill>
          <Pill tone="warning">Flat ~{LIVE.flatHours}h</Pill>
          <Pill tone="info">0 opens since Oct 10</Pill>
          <Pill tone="danger">−$6.70 vs fair HODL</Pill>
        </Row>
      </Stack>

      <Grid columns={4} gap={12}>
        <Stat value={`$${MONEY_IN}`} label="Money in" />
        <Stat value={`$${LIVE.moneyOut}`} label="Money out" />
        <Stat value="−$6.70" label="vs HODL funded + $38" tone="danger" />
        <Stat value="−$7.93" label="vs basis $157.56" tone="warning" />
      </Grid>

      <Callout tone="warning" title="Capital is idle">
        No open LP since the in-range close at 2026-10-10 05:42:17Z (tx
        9Z3om8uz…). Past-limit recycle was not run: that path is for a stranded
        LP, and the wallet is flat. The Mac API is refused from this VM, so the
        reporter and watchdog were not restarted. Rebalance volume right now is
        zero. The −$0.28 versus the Oct 10 mark is the same SOL bag at a lower
        spot, not a fee or a trade.
      </Callout>

      <Card>
        <CardHeader trailing={<Text size="small">USD</Text>}>
          Strategy mark vs fair HODL
        </CardHeader>
        <CardBody>
          <LineChart
            categories={DAILY.map((p) => p.t)}
            series={[
              {
                name: "Strategy (wallet + LP)",
                data: DAILY.map((p) => p.equity),
                tone: "info",
              },
              {
                name: "HODL funded bag, +$38 from Oct 6",
                data: DAILY.map((p) => p.hodl),
                tone: "neutral",
              },
            ]}
            referenceLines={[
              { value: MONEY_IN, label: "Money in $119.56", tone: "warning" },
              { value: BASIS, label: "Basis $157.56", tone: "neutral" },
            ]}
            height={280}
          />
          <Text size="small" tone="secondary" style={{ marginTop: 8 }}>
            Daily chain marks, not reporter snapshots. Both lines step up $38
            on Oct 6 (inbound USDC 5D9ercnv…, memo 1791261839279249303). That
            transfer is not fee income. Ex-transfer book today is{" "}
            {"$" + LIVE.exTransfer.toFixed(2)}.
          </Text>
        </CardBody>
      </Card>

      <Grid columns={2} gap={16}>
        <Card>
          <CardHeader>Scorecard</CardHeader>
          <CardBody>
            <Table headers={["Item", "Value"]} rows={SCORE} />
          </CardBody>
        </Card>
        <Card>
          <CardHeader>Rebalance volume</CardHeader>
          <CardBody>
            <Table headers={["Window", "Count"]} rows={VOLUME} />
            <Text size="small" tone="secondary" style={{ marginTop: 8 }}>
              Cup slots are full. The 1.0% / 0.05 book last opened on Sep 28.
              The five Cup-window opens were ~16% bands. Pending fees{" "}
              {"$" + LIVE.pendingFees.toFixed(2)}.
            </Text>
          </CardBody>
        </Card>
      </Grid>

      <Card>
        <CardHeader>This run</CardHeader>
        <CardBody>
          <Table headers={["Check", "Result"]} rows={OPS} />
        </CardBody>
      </Card>

      <Divider />

      <Stack gap={6}>
        <H2>What the mark is</H2>
        <Text>
          Money out ${LIVE.moneyOut} is the flat wallet at spot ${LIVE.spot}.
          Versus the original ${MONEY_IN} that is +${LIVE.vsIn}. Versus a HODL
          of the funded bag alone (${LIVE.hodlFunded}) the gap looks like +$31,
          because the wallet still holds the extra $38. The fair comparison is
          HODL of that funded bag plus the $38 cash (${LIVE.hodlFair}), which
          the book trails by $6.70.
        </Text>
        <Text size="small" tone="secondary">
          Orca / Solana only. Width and threshold were not edited. No Condor
          agent LP. Ledger T013 remains SUPERSEDED until a new trial row is
          written on purpose.
        </Text>
      </Stack>
    </Stack>
  );
}
