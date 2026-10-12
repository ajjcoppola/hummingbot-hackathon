import {
  Callout,
  Card,
  CardBody,
  CardHeader,
  Divider,
  Grid,
  H1,
  H2,
  H3,
  LineChart,
  BarChart,
  Pill,
  Row,
  Stack,
  Stat,
  Table,
  Text,
} from "cursor/canvas";

/** Deposit mark: 100.25 USDC + 0.16535 SOL at $116.77. */
const MONEY_IN = 119.56;
/** Same bag plus the 2026-10-06 inbound 38 USDC. */
const BASIS = 157.56;

const READ = {
  at: "2026-10-12 14:07Z",
  slot: "456073845",
  spot: 110.034,
  tick: -22071,
  sol: 0.6459383,
  usdc: 79.009155,
  moneyOut: 150.08,
  exTransfer: 112.08,
  hodlBag: 118.44,
  hodlPlus38: 156.44,
  vsIn: 30.52,
  vsBasis: -7.48,
  vsHodl38: -6.36,
  vsPrior: 0.45,
  flatHours: 56.4,
  opens: 103,
};

/** Ex-transfer mark vs HODL of the original funded bag. The $38 inbound is left out of both lines. */
const DAILY = [
  { t: "9/30", ex: 119.69, hodl: 119.93 },
  { t: "10/1", ex: 118.96, hodl: 119.71 },
  { t: "10/2", ex: 121.83, hodl: 120.48 },
  { t: "10/3", ex: 120.22, hodl: 119.96 },
  { t: "10/4", ex: 121.71, hodl: 120.37 },
  { t: "10/5", ex: 121.12, hodl: 120.21 },
  { t: "10/6", ex: 121.2, hodl: 120.23 },
  { t: "10/7", ex: 118.34, hodl: 119.44 },
  { t: "10/8", ex: 115.46, hodl: 118.84 },
  { t: "10/9", ex: 111.72, hodl: 118.36 },
  { t: "10/10", ex: 111.91, hodl: 118.4 },
  { t: "10/11", ex: 111.63, hodl: 118.33 },
  { t: "10/12", ex: 112.08, hodl: 118.44 },
];

const RECENT = [
  ["10/06", "$120.86", "$159.20", "$121.20", "+$0.97"],
  ["10/07", "$116.07", "$156.34", "$118.34", "−$1.10"],
  ["10/08", "$112.45", "$153.46", "$115.46", "−$3.39"],
  ["10/09", "$109.51", "$149.72", "$111.72", "−$6.64"],
  ["10/10", "$109.77", "$149.91", "$111.91", "−$6.49"],
  ["10/11", "$109.32", "$149.63", "$111.63", "−$6.70"],
  ["10/12", "$110.03", "$150.08", "$112.08", "−$6.36"],
];

const WIDTHS = [
  ["~1.5% (Sep 25, before 18:44Z)", "12"],
  ["~1.0% (through 23:09Z Sep 28)", "81"],
  ["~16.08% log, 1608 ticks", "7"],
  ["~16.0% price ratio, 1488 ticks", "3"],
];

export default function T013MainnetCup() {
  return (
    <Stack gap={24} style={{ padding: 24, maxWidth: 980 }}>
      <Stack gap={8}>
        <H1>T013 mainnet — money in, money out</H1>
        <Text tone="secondary">
          Orca SOL/USDC Czfq3xZZ. Chain mark at {READ.at}, slot {READ.slot}.
          Money in is the deposit bag, $119.56. Ledger row T013 stays
          SUPERSEDED; this canvas is a public-RPC mark, and it does not add a
          race P&amp;L row.
        </Text>
        <Row gap={8} wrap>
          <Pill active>ACTION</Pill>
          <Pill>Flat {READ.flatHours}h</Pill>
          <Pill>No open LP</Pill>
          <Pill>API down</Pill>
        </Row>
      </Stack>

      <Grid columns={4} gap={12}>
        <Stat value={`$${MONEY_IN}`} label="Money in (deposit mark)" />
        <Stat value={`$${READ.moneyOut.toFixed(2)}`} label="Money out (wallet)" />
        <Stat
          value="−$6.36"
          label="vs HODL + $38 cash"
          tone="danger"
        />
        <Stat value={String(READ.opens)} label="On-chain opens since Sep 25" />
      </Grid>

      <Grid columns={4} gap={12}>
        <Stat value="n/a" label="In-range % (no clean marks)" tone="warning" />
        <Stat value="$0" label="Pending fees" />
        <Stat value="None" label="Current LP" tone="danger" />
        <Stat value="ACTION" label="Verdict" tone="warning" />
      </Grid>

      <Callout tone="danger" title="ACTION — capital is idle">
        Wallet flat since the in-range close at 2026-10-10 05:42:17Z (~56.4h).
        Spot $110.034 (tick −22071) with 0.645938300 SOL and 79.009155 USDC.
        No Token-2022 position. The past-limit recycle path applies to a
        stranded LP; this wallet has none, so adopt --recycle was not run.
        Hummingbot API :8000 and gateway :15888 refused. Watchdog restart
        stays on the Mac LaunchAgent — MAINNET_OPS.md has no nohup command,
        and this VM is not the race host.
      </Callout>

      <Card>
        <CardHeader trailing={<Text size="small">USD</Text>}>
          Ex-transfer mark vs HODL of the funded bag
        </CardHeader>
        <CardBody>
          <LineChart
            categories={DAILY.map((p) => p.t)}
            series={[
              {
                name: "Strategy ex-$38 transfer",
                data: DAILY.map((p) => p.ex),
                tone: "info",
              },
              {
                name: "HODL 100.25 USDC + 0.16535 SOL",
                data: DAILY.map((p) => p.hodl),
                tone: "neutral",
              },
            ]}
            beginAtZero={false}
            yMin={108}
            yMax={124}
            referenceLines={[
              { value: MONEY_IN, label: "Money in $119.56", tone: "warning" },
            ]}
            height={260}
          />
          <Text size="small" tone="secondary" style={{ marginTop: 8 }}>
            Daily chain marks, 14:00Z reads. From Oct 6 the strategy line
            subtracts the $38 inbound so the gap is inventory, not the
            transfer. The book holds 0.646 SOL against the 0.16535 SOL deposit,
            so spot moves the mark more than HODL.
          </Text>
        </CardBody>
      </Card>

      <Stack gap={8}>
        <H2>Since the $38 inbound</H2>
        <Text tone="secondary" size="small">
          Money out is the wallet mark. Ex-transfer subtracts $38. The last
          column is money out minus HODL of the funded bag plus that $38
          (basis $157.56).
        </Text>
        <Table
          headers={["Day", "Spot", "Money out", "Ex-transfer", "vs HODL+$38"]}
          columnAlign={["left", "right", "right", "right", "right"]}
          rows={RECENT}
          rowTone={[
            undefined,
            undefined,
            undefined,
            "danger",
            "danger",
            "danger",
            "danger",
          ]}
          striped
        />
      </Stack>

      <Grid columns={2} gap={16}>
        <Stack gap={8}>
          <H3>Rebalance volume</H3>
          <BarChart
            horizontal
            categories={WIDTHS.map((w) => w[0])}
            series={[
              { name: "Successful opens", data: [12, 81, 7, 3], tone: "info" },
            ]}
            height={180}
          />
          <Text size="small" tone="secondary">
            103 successful opens since 2026-09-25. Last ~1.0% open was
            2026-09-28 23:09Z. Cup window (Oct 7 02:00Z–Oct 9 02:00Z) had 5
            opens, all ~16%. Opens since the Oct 10 close: 0. Reporter
            n_rebals is unavailable — snapshot dir
            data/devnet_runs/T013_mainnet_100_width1_20260925 is absent.
          </Text>
        </Stack>
        <Stack gap={8}>
          <H3>This read</H3>
          <Table
            headers={["Item", "Value"]}
            rows={[
              ["Verdict", "ACTION"],
              ["Current LP", "None"],
              ["In-range %", "No clean marks"],
              ["Pending fees", "$0"],
              ["On-chain opens", "103"],
              ["Reporter n_rebals", "Unavailable"],
              ["CollectFeesV2", "103"],
              ["Failed opens", "9"],
              ["YAML", "1.0% / 0.05 unchanged"],
            ]}
            rowTone={["warning", "danger", "warning"]}
            striped
          />
        </Stack>
      </Grid>

      <Divider />

      <Stack gap={6}>
        <H2>How the $150.08 breaks down</H2>
        <Text>
          Wallet only: 0.645938300 SOL × $110.034 + 79.009155 USDC = $150.08.
          Versus the $119.56 deposit mark that is +$30.52, and $38.00 of that
          is the 2026-10-06 inbound transfer. Versus basis $157.56 the mark is
          −$7.48. Versus HODL of the funded bag plus $38 cash ($156.44) it is
          −$6.36. The +$0.45 since the Oct 11 mark ($149.63 at $109.324) is
          the same SOL and USDC balances marked at $110.034.
        </Text>
        <Text size="small" tone="secondary">
          Last fee event remains the Oct 10 close: 0.000387825 SOL + 0.044227
          USDC. No signature after the 05:42:28Z fanout 4CqwxugJ…. Status at
          14:06:45Z returned ok false. Docker :2375 was up with zero
          containers. Width and threshold were left unchanged.
        </Text>
      </Stack>
    </Stack>
  );
}
