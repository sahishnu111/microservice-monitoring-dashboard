# SLO Tracking & Error Budget

## Definitions
- **SLO**: each service should be available **99.5%** of the time (`service:slo_target:ratio = 0.995`).
- **Availability** = `1 - (5xx requests / all requests)`. `/metrics` scrapes are excluded. `/load-test` is included on purpose so you can demo budget burn.
- **Error budget** = the 0.5% of requests allowed to fail. *Remaining* = `1 - error_ratio / 0.005`, clamped to 0–100%.
- **Burn rate** = `error_ratio / 0.005`. 1x uses the budget exactly over the SLO window; 14.4x would use a 30-day budget in ~2 days.

A real SLO uses a 30-day window. For a local demo, the dashboard calculates the budget over the selected Grafana time range (`$__range`).

## Recording rules (`monitoring/prometheus/slo-rules.yml`)
| Rule | Meaning |
|---|---|
| `service:availability:ratio_rate5m` | availability over 5m per service; services with no traffic show 1 |
| `service:availability:ratio_rate1h` | same over 1h (used by the alert) |
| `service:slo_target:ratio` | constant 0.995 per service |

## Alert
`ErrorBudgetBurnHigh` (critical) fires when the error ratio is above `14.4 * 0.005` (7.2%) over **both** 5m and 1h, traffic is above 0.1 req/s, and this lasts for 2m.

## Dashboard queries (`SLO & Error Budget`, uid `slo-error-budget`)
- Current availability: `100 * service:availability:ratio_rate5m` (green at ≥ 99.5)
- Budget remaining: `clamp(100 * (1 - (errors[$__range] / total[$__range]) / (1 - 0.995)), 0, 100)`
- Burn rate: `(1 - service:availability:ratio_rate5m) / (1 - 0.995)`, with threshold lines at 1x and 14.4x

## Demo
```bash
docker compose up -d
for i in $(seq 1 300); do curl -s -o /dev/null "http://localhost:8002/load-test?error_rate=0.3"; sleep 0.2; done
```
order-service's availability drops to about 70%, its budget goes to 0%, and its burn rate is about 60x. `ErrorBudgetBurnHigh` goes to pending, then fires once the 1h window passes 7.2% and the 2m `for` has passed.

## Tests
```bash
promtool test rules monitoring/prometheus/tests/slo-rules.test.yml
```
