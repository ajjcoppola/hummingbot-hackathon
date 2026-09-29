import {
  Callout,
  Divider,
  Grid,
  H1,
  H2,
  LineChart,
  Row,
  Stack,
  Stat,
  Table,
  Text,
} from "cursor/canvas";

const DAYS = [
  "Sep 7", "Sep 8", "Sep 9", "Sep 10", "Sep 11", "Sep 12", "Sep 13",
  "Sep 14", "Sep 15", "Sep 16", "Sep 17", "Sep 18", "Sep 19", "Sep 20",
  "Sep 21", "Sep 22", "Sep 23", "Sep 24", "Sep 25", "Sep 26", "Sep 27", "Sep 28",
];

/** Live rules: width 1.0, thr 0.05, high-low path, 20x share (canvas baseline). */
const BASELINE_LP = [
  792.6, 729.0, 673.9, 586.2, 551.6, 514.5, 482.7, 425.4, 391.9, 381.2, 368.6,
  363.6, 344.2, 329.9, 321.0, 304.7, 285.4, 276.1, 270.2, 259.1, 252.6, 242.8,
];
const HODL = [
  796.7, 794.4, 787.3, 778.7, 793.0, 790.1, 780.4, 793.1, 771.5, 778.9, 789.5,
  831.6, 826.6, 826.0, 854.2, 854.5, 841.0, 847.3, 868.5, 863.7, 866.6, 857.7,
];
/** SitWide 16% full width, 1x share, no recenter. */
const SIT_WIDE = [
  796.8, 795.3, 787.7, 775.7, 798.1, 795.0, 781.5, 800.6, 768.2, 783.1, 799.9,
  828.2, 828.4, 829.4, 830.5, 830.5, 830.5, 830.6, 830.6, 830.6, 830.6, 830.6,
];
/** Holdout-promoted: live_rebalancer width 16%, thr 0.5, 1x share. */
const PROMOTED = [
  796.8, 795.3, 787.7, 743.1, 763.6, 760.8, 748.6, 732.5, 705.8, 718.4, 732.4,
  755.3, 752.0, 752.4, 769.8, 771.4, 768.2, 772.5, 780.0, 777.1, 780.6, 774.8,
];

export default function CupMoneySearch() {
  return (
    <Stack gap={20}>
      <Stack gap={6}>
        <H1>Cup money search — $800 Czfq3xZZ</H1>
        <Text tone="secondary">
          Offline R002. Napkin gate: fees and in-range loss scale together. Baseline is the live 1% band. Sit-wide and the holdout survivor are candidates only. T016 was not touched.
        </Text>
      </Stack>

      <Callout tone="warning" title="Simulation only — not live P&L">
        Concentration multiplies fee and LVR. Promotion requires the 1x book. A row that needs 200x is rejected. Pool fee intensity on 28 Sep was about 0.29%/day if you owned every dollar of liquidity; an $800 1x share is about $2.35/day of pool fees before concentration.
      </Callout>

      <Row gap={16}>
        <Stat value="$243" label="Baseline end (1% band, 20x)" tone="danger" />
        <Stat value="$831" label="Sit-wide 16% end (1x)" />
        <Stat value="$775" label="Promoted 16%/0.5 end (1x)" />
        <Stat value="$858" label="Hold opening mix" />
      </Row>

      <H2>Equity vs hold</H2>
      <Text tone="secondary">
        Vertical axis is mark-to-market USDC. Horizontal axis is UTC date. Baseline uses the live width 1.0 / threshold 0.05 path that matched the earlier canvas (~$243). Sit-wide opens once at 16% full width. Promoted is live_rebalancer at 16% / 0.5 on the 1x book (holdout median 48h edge positive on both paths; train edge was negative — thin promote, not deployed).
      </Text>
      <LineChart
        categories={DAYS}
        series={[
          { name: "Baseline live 1% (20x share)", data: BASELINE_LP, tone: "danger" },
          { name: "Sit-wide 16% (1x)", data: SIT_WIDE, tone: "info" },
          { name: "Promoted 16%/0.5 (1x)", data: PROMOTED, tone: "success" },
          { name: "Hold opening mix", data: HODL, tone: "neutral" },
        ]}
        beginAtZero={false}
        valuePrefix="$"
        height={300}
      />
      <Text size="small" tone="tertiary">
        Source: GeckoTerminal hourly OHLCV Czfq3xZZ, 2026-09-07 through 2026-09-28. Runner: research/cup_money_search.py. Artifact: data/cup_grid_20260928.json.
      </Text>

      <Divider />

      <H2>What passed the napkin</H2>
      <Table
        headers={["Rule", "Train edge", "Holdout edge", "End vs hold", "Decision"]}
        rows={[
          [
            "Live 1.0 / 0.05 (baseline)",
            "deeply negative",
            "deeply negative",
            "$243 vs $858",
            "FAIL — reproduces the loss",
          ],
          [
            "Sit-wide 16%",
            "+$1.82 / 48h",
            "−$1.38 / 48h",
            "$831 vs $856",
            "NO_PROMOTE — train only",
          ],
          [
            "Live 16% / thr 0.5",
            "−$4.17 / 48h",
            "+$0.38 / +$0.60",
            "$775 vs $856 full window",
            "PROMOTE holdout — not deployed",
          ],
          [
            "Do-not-chase 8% / trend 0.04",
            "−$1.27 / 48h",
            "+$0.17 / +$0.06",
            "$747 vs $857 full window",
            "PROMOTE holdout — not deployed",
          ],
        ]}
      />

      <Grid columns={2} gap={16}>
        <Stack gap={4}>
          <Text weight="semibold">Higher fee tiers (API only)</Text>
          <Text tone="secondary">
            Orca listed 18 SOL-USDC pools with fee greater than 0.04% and intensity above this whirlpool. Example: BofA2ViU… at 0.16% with about 1.76%/day intensity. No OHLCV was pulled for them in R002, so no SitWide replay and no invented address in a config.
          </Text>
        </Stack>
        <Stack gap={4}>
          <Text weight="semibold">Honest Cup story</Text>
          <Text tone="secondary">
            A 1% band that recenters is the wrong prior. Wide + rare recenter is the only shape that stayed near hold. Machine learning as a center-picker for a tight band is not enough. A chop gate is the only ML-shaped idea that fits the napkin.
          </Text>
        </Stack>
      </Grid>
    </Stack>
  );
}
