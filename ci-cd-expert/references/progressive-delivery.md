# Progressive Delivery & Canary Analysis

## Canary Deployment

Route fraction of traffic (1-5%) to new application version. Automated Canary Analysis (ACA) removes human error, fatigue, bias.

---

## Spinnaker & Kayenta Architecture

- **Spinnaker**: Orchestrator. Provisions baseline (production version) and canary (new version) side-by-side.
- **Kayenta**: Statistical comparison engine. Compares metrics between canary and baseline, scores differences.

### Automated Canary Workflow
```
Deploy Canary & Baseline (1% Traffic)
       │
       ▼
Kayenta fetches metrics (Prometheus/Datadog)
       │
       ▼
Statistical comparison: Mann-Whitney U test
       │
 ┌─────┴────────────────────────┐
 │                              │
 ▼                              ▼
Score < Threshold              Score >= Threshold
(Auto-Rollback)                (Auto-Promote)
```

---

## Kayenta Configuration Example

```json
{
  "name": "api-canary-analysis",
  "judge": {
    "name": "NetflixACAJudge-v1.0",
    "judgeConfigurations": {}
  },
  "metrics": [
    {
      "name": "error-rate",
      "query": {
        "type": "prometheus",
        "customInlineTemplate": "sum(rate(http_requests_total{status=~'5..'}[5m]))"
      },
      "analysisConfigurations": {
        "canary": {
          "direction": "increase",
          "nanStrategy": "replace",
          "critical": true,
          "mustHaveData": true
        }
      }
    }
  ],
  "classifier": {
    "groupWeights": {
      "reliability": 70,
      "latency": 30
    }
  }
}
```

---

## Statistical Parameters

| Metric / Parameter | Function | Value / Choice |
|--------------------|----------|----------------|
| `direction` | Bad trend flag | `increase` (errors), `decrease` (throughput) |
| `nanStrategy` | Handling missing points | `replace` with 0 (errors), `remove` (latency) |
| `outlierFactor` | IQR filter (hides spikes) | `3.0` (exclude values above Q3 + 3*IQR) |
| `critical` | Hard abort flag | `true` (fails run immediately if bad) |

---

## Common Mistakes

- Comparing canary against overall production instead of a newly launched baseline.
- Analysis times too short (e.g. 5 minutes). Minimum 30-60 minutes recommended for statistical validity.
- Not flagging error rates as critical, leading to latency passes masks major code exceptions.
