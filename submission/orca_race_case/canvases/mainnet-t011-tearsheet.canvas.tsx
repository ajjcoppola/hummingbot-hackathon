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
  useHostTheme,
} from "cursor/canvas";

const META = {
  hours: 6.93,
  eq0: 120.29,
  eq1: 120.66,
  d_eq: 0.37,
  in_range_pct: 96.8,
  n_rebals: 3,
  fee_q_end: 0.01018,
  price0: 117.08,
  price1: 116.66,
  bot_uptime: 100.0,
  flat_polls: 4,
};

const LIVE = {
  ts: "2026-09-25T04:33:28Z",
  bot: "orca_tight_mainnet_smoke-20260924-213341",
  lp: "FoFux4jMFsHjESBZcjujxNZCTQPaFKGL5wBeXQBAgktx",
  in_range: true,
  price: 116.65,
  lower: 116.4,
  upper: 118.14,
  lp_sol: 0.732,
  lp_usdc: 14.22,
  wallet_sol: 0.1004,
  wallet_usdc: 9.35,
  equity_approx: 120.6,
  pending_fee_usdc: 0.0099,
};

const EQUITY = [
  { t: "21:38", equity: 120.29, price: 117.08 },
  { t: "21:58", equity: 120.22, price: 116.95 },
  { t: "22:16", equity: 119.94, price: 116.51 },
  { t: "22:42", equity: 119.76, price: 116.28 },
  { t: "23:03", equity: 120.03, price: 116.64 },
  { t: "23:29", equity: 120.22, price: 116.95 },
  { t: "23:59", equity: 120.26, price: 117.02 },
  { t: "00:18", equity: 120.44, price: 117.47 },
  { t: "00:42", equity: 120.47, price: 117.62 },
  { t: "01:08", equity: 120.5, price: 117.77 },
  { t: "01:37", equity: 120.34, price: 117.19 },
  { t: "02:01", equity: 120.43, price: 117.46 },
  { t: "02:23", equity: 120.82, price: 118.23 },
  { t: "02:48", equity: 120.6, price: 117.04 },
  { t: "03:16", equity: 120.61, price: 117.09 },
  { t: "03:40", equity: 120.59, price: 117.01 },
  { t: "04:01", equity: 120.55, price: 116.86 },
  { t: "04:21", equity: 120.45, price: 116.43 },
  { t: "04:29", equity: 120.57, price: 116.56 },
];

const JOURNEY = [
  {
    when: "Sep 23",
    step: "T009 open",
    detail: "Funded ~$100 + SOL gas. Threshold 0.8. Pos H84XDs3p… then stall OOR, 0 rebals.",
  },
  {
    when: "Sep 24 AM",
    step: "Orphan",
    detail: "adopt stopped bot; LP FZf1… unmanaged. Soft-restart could not attach.",
  },
  {
    when: "Sep 24 21:33Z",
    step: "T010 recycle",
    detail: "Closed FZf1…; threshold → 0.05; managed OPEN DWhducqt…",
  },
  {
    when: "Sep 25 ~02:09Z+",
    step: "T011 rebals",
    detail: "3 close→open cycles. Lineage DWhducqt → E2g8SvNn → 88Mk1fb5 → FoFux4jM (live).",
  },
];

const POSITIONS = [
  { short: "DWhducqt", polls: 126, role: "T010 open → first band" },
  { short: "E2g8SvNn", polls: 3, role: "Brief after 1st rebal" },
  { short: "88Mk1fb5", polls: 53, role: "Mid-window band" },
  { short: "FoFux4jM", polls: 7, role: "Current LP (in-range)" },
];

export default function MainnetT011Tearsheet() {
  const theme = useHostTheme();

  return (
    <Stack gap={24} style={{ padding: 24, maxWidth: 960 }}>
      <Stack gap={8}>
        <H1>Mainnet account tearsheet</H1>
        <Text tone="secondary">
          Orca SOL-USDC · wallet 2ZuShDjg… · T011 window ~{META.hours}h · marks
          exclude rebalance flaps · not audited race P&amp;L
        </Text>
        <Row gap={8} style={{ flexWrap: "wrap" }}>
          <Pill tone="success">in-range</Pill>
          <Pill tone="success">bot running</Pill>
          <Pill tone="info">{META.n_rebals} rebals (gate PASS)</Pill>
          <Pill>width 1.5% / thr 0.05%</Pill>
        </Row>
      </Stack>

      <Grid columns={4} gap={12}>
        <Stat value={`$${LIVE.equity_approx}`} label="Marked equity (USDC)" />
        <Stat
          value={`+$${META.d_eq}`}
          label="T011 Δ MTM (~7h)"
          tone="success"
        />
        <Stat value={`${META.in_range_pct}%`} label="In-range (clean)" />
        <Stat value={`${META.n_rebals}`} label="Close→open cycles" />
      </Grid>

      <Callout tone="info" title="Where capital sits now">
        Free {LIVE.wallet_sol} SOL + ${LIVE.wallet_usdc} USDC · LP{" "}
        {LIVE.lp_sol} SOL + ${LIVE.lp_usdc} USDC · band [{LIVE.lower},{" "}
        {LIVE.upper}] @ {LIVE.price} · pending fees ~${LIVE.pending_fee_usdc} ·
        bot {LIVE.bot}
      </Callout>

      <Card>
        <CardHeader>Marked equity (clean polls)</CardHeader>
        <CardBody>
          <LineChart
            categories={EQUITY.map((p) => p.t)}
            series={[
              {
                name: "Equity (USDC)",
                data: EQUITY.map((p) => p.equity),
                tone: "info",
              },
            ]}
            height={220}
          />
          <Text size="small" tone="secondary" style={{ marginTop: 8 }}>
            Source: T011 reporter snapshots · pool-priced marks only · Y ≈
            $119.7–$120.8 · spot drifted {META.price0} → {META.price1}
          </Text>
        </CardBody>
      </Card>

      <Grid columns={2} gap={16}>
        <Card>
          <CardHeader>How we got here</CardHeader>
          <CardBody>
            <Table
              headers={["When", "Step", "What happened"]}
              rows={JOURNEY.map((j) => [j.when, j.step, j.detail])}
            />
          </CardBody>
        </Card>
        <Card>
          <CardHeader>LP lineage (T011)</CardHeader>
          <CardBody>
            <Table
              headers={["Position", "Polls", "Role"]}
              rows={POSITIONS.map((p) => [p.short + "…", String(p.polls), p.role])}
            />
            <Text size="small" tone="secondary" style={{ marginTop: 8 }}>
              Flat polls during close/open: {META.flat_polls}. Bot uptime{" "}
              {META.bot_uptime}%.
            </Text>
          </CardBody>
        </Card>
      </Grid>

      <Divider />

      <Stack gap={8}>
        <H2>Read carefully</H2>
        <Text>
          Naive reporter start MTM (~$67) ignored LP SOL when pool_price was 0 —
          ignore that Δ. Clean marks show ~flat capital with fee accrual while
          rebalancing finally works after the 0.05 threshold cut.
        </Text>
        <Text tone="secondary" size="small">
          Artifacts: data/devnet_runs/T011_…/tearsheet.md · docs/TRIALS_LEDGER.md
          T010–T011 · live LP {LIVE.lp.slice(0, 8)}…
        </Text>
        <Text size="small" style={{ color: theme.tokens.text.tertiary }}>
          Snapshot {LIVE.ts}
        </Text>
      </Stack>
    </Stack>
  );
}
