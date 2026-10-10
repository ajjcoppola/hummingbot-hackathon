import {
  BarChart,
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

const MONTHS: string[] = ["2023-01", "2023-02", "2023-03", "2023-04", "2023-05", "2023-06", "2023-07", "2023-08", "2023-09", "2023-10", "2023-11", "2023-12", "2024-01", "2024-02", "2024-03", "2024-04", "2024-05", "2024-06", "2024-07", "2024-08", "2024-09", "2024-10", "2024-11", "2024-12", "2025-01", "2025-02", "2025-03", "2025-04", "2025-05", "2025-06", "2025-07", "2025-08", "2025-09", "2025-10", "2025-11", "2025-12", "2026-01", "2026-02", "2026-03", "2026-04", "2026-05", "2026-06", "2026-07", "2026-08", "2026-09"];
const WEALTH: Record<string, number[]> = {"spy_plain": [6.29, 3.62, 7.46, 9.18, 9.68, 16.79, 20.62, 18.66, 13.03, 10.58, 20.68, 26.19, 28.2, 34.89, 39.3, 33.69, 40.45, 45.41, 47.17, 50.61, 53.77, 52.4, 61.49, 57.59, 61.83, 59.77, 50.87, 49.56, 58.96, 67.13, 70.98, 74.49, 80.7, 85.01, 85.37, 85.51, 88.25, 86.62, 77.41, 96.05, 106.37, 104.24, 104.31, 109.78, 111.48], "qm_screen": [12.09, 6.1, 17.25, 22.16, 12.72, 24.71, 24.09, 18.23, 12.16, 20.69, 31.45, 38.78, 41.51, 59.94, 78.02, 66.31, 79.79, 75.6, 89.26, 85.69, 94.22, 104.66, 133.38, 115.92, 138.2, 127.88, 132.42, 142.93, 153.2, 159.37, 162.32, 169.79, 196.71, 185.05, 182.32, 184.67, 206.27, 213.29, 187.17, 204.48, 209.3, 181.42, 197.0, 235.55, 224.67], "qm_fill": [10.86, 5.05, 16.05, 20.92, 11.43, 23.32, 22.62, 16.8, 10.78, 19.12, 29.5, 36.8, 39.42, 58.23, 75.28, 63.98, 76.9, 72.36, 86.04, 80.8, 88.81, 99.05, 127.1, 109.84, 131.39, 121.81, 124.22, 131.27, 140.22, 145.8, 148.43, 154.96, 179.79, 168.76, 167.29, 168.74, 189.17, 200.54, 175.49, 191.46, 196.6, 170.16, 184.95, 221.91, 211.38], "spy_overlay": [18.24, 12.52, 26.99, 29.99, 26.96, 37.94, 41.56, 34.24, 26.03, 34.92, 49.44, 60.79, 62.38, 87.37, 106.5, 91.11, 107.54, 107.81, 118.12, 115.13, 128.16, 135.43, 166.78, 155.64, 172.25, 157.5, 153.35, 162.77, 177.36, 191.92, 203.32, 208.91, 238.37, 246.3, 236.57, 236.62, 253.98, 242.1, 212.45, 241.59, 252.87, 212.17, 217.5, 257.35, 259.7]};
const DRAWDOWN: Record<string, number[]> = {"spy_plain": [0.0, -4.92, -1.39, 0.0, -0.55, 0.0, 0.0, -1.63, -6.29, -8.32, 0.0, -0.29, -1.71, 0.0, -0.02, -4.05, -0.75, -0.46, -2.49, -0.21, 0.0, -2.73, 0.0, -3.25, -1.3, -3.06, -8.46, -9.25, -3.55, 0.0, -0.79, -0.6, -0.1, -0.78, -0.58, -1.23, -0.51, -1.37, -6.23, 0.0, 0.0, -1.43, -1.4, -1.39, -0.59], "qm_screen": [0.0, -5.87, 0.0, -1.28, -8.9, 0.0, -1.85, -6.49, -11.29, -4.54, 0.0, -1.34, -1.92, 0.0, 0.0, -7.57, -2.83, -5.1, -0.56, -2.44, -1.61, -2.5, -0.38, -8.18, -1.43, -6.03, -4.16, -0.67, -0.98, 0.0, -2.96, -1.99, 0.0, -6.21, -7.11, -6.34, -6.2, -4.05, -12.05, -6.75, -5.28, -13.81, -9.04, -2.77, -5.92], "qm_fill": [0.0, -5.76, 0.0, -1.26, -9.01, 0.0, -1.9, -6.56, -11.37, -4.7, 0.0, -1.34, -1.93, 0.0, 0.0, -7.48, -2.96, -5.45, -0.42, -3.22, -1.65, -2.5, -0.41, -8.28, -1.36, -5.79, -4.77, -1.77, -0.99, 0.0, -2.99, -2.29, 0.0, -6.22, -6.73, -6.22, -6.27, -2.58, -10.7, -5.52, -3.86, -12.43, -7.63, -2.78, -5.96], "spy_overlay": [0.0, -7.62, 0.0, -1.53, -3.82, 0.0, -0.72, -5.85, -11.61, -5.38, -0.3, -1.55, -2.26, 0.0, 0.0, -8.85, -3.28, -3.16, -3.27, -4.6, -0.97, -3.6, -0.17, -6.61, -1.28, -7.53, -9.02, -5.64, -1.62, 0.0, -1.95, -2.19, 0.0, -2.37, -5.11, -5.1, -5.97, -9.12, -17.0, -9.26, -6.26, -17.07, -15.66, -5.07, -4.45]};

export default function QmVsSpyOverlay() {
  return (
    <Stack gap={20}>
      <Stack gap={6}>
        <H1>Amir swap: SPY equity vs HRP×m under the same overlays</H1>
        <Text tone="secondary">
          Both books use expanding vol cap + 0.40 GLD + 0.25 BTC (BITO proxy).
          Only the equity sleeve changes: top-60 HRP × quantum m versus plain SPY.
          Window 2023-01-03 to 2026-09-25, 936 sessions.
        </Text>
        <Row gap={8}>
          <Pill tone="warning">SPY sleeve wins CAGR</Pill>
          <Pill tone="success">HRP×m sleeve wins drawdown</Pill>
          <Pill tone="info">Live BTC sleeve: IBIT</Pill>
        </Row>
      </Stack>

      <Grid columns={4} gap={12}>
        <Stat value="40.99%" label="SPY + overlays CAGR" tone="warning" />
        <Stat value="35.64%" label="HRP×m fill CAGR" tone="info" />
        <Stat value="−20.44%" label="SPY + overlays max DD" tone="danger" />
        <Stat value="−13.28%" label="HRP×m fill max DD" tone="success" />
      </Grid>

      <Callout tone="warning" title="What replacing the sleeve does">
        Swap HRP×m for SPY and CAGR rises from 37.17% (screen) /
        35.64% (5 bps fill) to 40.99%,
        but the hole deepens from about −13.28% to −20.44%.
        Paired gap (SPY overlay − QM screen) is +3.1 pp/yr, Newey–West t = 0.67.
        Same story Amir found without Bitcoin: the stock book is not the return engine; the overlays are.
      </Callout>

      <Card>
        <CardHeader>Month-end cumulative return</CardHeader>
        <CardBody>
          <LineChart
            height={300}
            categories={MONTHS}
            series={[
              { name: "SPY (no overlay)", data: WEALTH["spy_plain"], tone: "neutral" },
              { name: "HRP×m + overlays (screen)", data: WEALTH["qm_screen"], tone: "info" },
              { name: "HRP×m + overlays (5 bps fill)", data: WEALTH["qm_fill"], tone: "info" },
              { name: "SPY + overlays (Amir swap)", data: WEALTH["spy_overlay"], tone: "warning" },
            ]}
            valueSuffix="%"
            beginAtZero={false}
          />
          <Text tone="secondary">Y-axis: cumulative return (%). Overlays are 0.40 GLD + 0.25 BITO on both active books.</Text>
        </CardBody>
      </Card>

      <Grid columns={2} gap={16}>
        <Card>
          <CardHeader>Drawdown at month end</CardHeader>
          <CardBody>
            <LineChart
              height={240}
              categories={MONTHS}
              series={[
                { name: "SPY (no overlay)", data: DRAWDOWN["spy_plain"], tone: "neutral" },
                { name: "HRP×m + overlays (screen)", data: DRAWDOWN["qm_screen"], tone: "info" },
                { name: "HRP×m + overlays (5 bps fill)", data: DRAWDOWN["qm_fill"], tone: "info" },
                { name: "SPY + overlays (Amir swap)", data: DRAWDOWN["spy_overlay"], tone: "warning" },
              ]}
              valueSuffix="%"
              beginAtZero={false}
            />
          </CardBody>
        </Card>
        <Card>
          <CardHeader>Paired gap (SPY overlay − QM screen)</CardHeader>
          <CardBody>
            <BarChart
              height={240}
              categories={["CAGR gap", "Sharpe gap×10", "MaxDD gap"]}
              series={[{
                name: "pp or units",
                data: [
                  3.06,
                  0.44,
                  -5.78,
                ],
                tone: "warning",
              }]}
              referenceLines={[{ value: 0, label: "0" }]}
            />
            <Text tone="secondary">
              CAGR and MaxDD in percentage points. Sharpe gap is ×10 so it fits the same axis
              (1.598 vs 1.554).
            </Text>
          </CardBody>
        </Card>
      </Grid>

      <Divider />
      <H2>Tearsheet</H2>
      <Table
        headers={["Metric", "SPY plain", "HRP×m screen", "HRP×m 5bps fill", "SPY + overlays"]}
        columnAlign={["left", "right", "right", "right", "right"]}
        striped
        rows={[["CAGR", "22.26%", "37.17%", "35.64%", "40.99%"], ["Total return", "111.48%", "224.67%", "211.38%", "259.70%"], ["Volatility", "14.94%", "21.97%", "22.16%", "23.28%"], ["Sharpe", "1.424", "1.554", "1.491", "1.598"], ["Max drawdown", "\u221218.76%", "\u221214.66%", "\u221213.28%", "\u221220.44%"], ["Calmar", "1.187", "2.536", "2.684", "2.006"], ["Feb\u2013Apr 2025", "\u221218.32%", "\u221211.06%", "\u221212.06%", "\u221216.45%"], ["Beta to SPY", "1.000", "0.898", "0.905", "1.144"], ["Corr to SPY", "1.000", "0.611", "0.610", "0.734"], ["Days", "936", "936", "936", "936"], ["Start", "2023-01-03", "2023-01-03", "2023-01-03", "2023-01-03"], ["End", "2026-09-25", "2026-09-25", "2026-09-25", "2026-09-25"]]}
      />
      <H2>Calendar years</H2>
      <Table
        headers={["Year", "SPY plain", "HRP×m screen", "HRP×m 5bps fill", "SPY + overlays"]}
        columnAlign={["left", "right", "right", "right", "right"]}
        striped
        rows={[["2023", "26.19%", "38.78%", "36.80%", "60.79%"], ["2024", "24.89%", "55.58%", "53.40%", "58.99%"], ["2025", "17.71%", "31.84%", "28.07%", "31.68%"], ["2026", "14.00%", "14.05%", "15.87%", "6.85%"]]}
      />
      <Text tone="secondary">
        Gross on the overlaid books is about 2.30× when equity scale is 1.0.
        Live Bitcoin symbol is IBIT; BITO is the backtest proxy. Research only — no IB orders.
      </Text>
    </Stack>
  );
}
