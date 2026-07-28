---
name: grafana
description: Grafana Cloud + IRM/OnCall access for the <org> stack. Covers token resolution, stack/IRM/OnCall API auth, and recipes for listing alert groups, alert payloads, and plugin settings. Use when working with Grafana Cloud, IRM, OnCall, alert groups, or anything under <stack>.grafana.net.
user_invocable: false
---

# Grafana Cloud / IRM / OnCall Access

Active stack: `<stack>.grafana.net` (instance ID `<INSTANCE_ID>`).
Old stack `terraform/grafana/<org>/` is deprecated — never modify.
SoT for tokens/IDs: `terraform/grafana/<stack>-monitoring/` outputs.

## Token Selection

| Need | Token | Header |
|---|---|---|
| Grafana stack API (`/api/...` on `<stack>.grafana.net`) | `grafana_sa_token` (TF output) | `Authorization: Bearer <token>` |
| OnCall API (`<oncall-host>.grafana.net`) | `grafana_sa_token` | `Authorization: <token>` (no Bearer) + `X-Grafana-Instance-ID: <INSTANCE_ID>` |
| Cloud Provider/Stack mgmt (rare) | `GRAFANA_CLOUD_ACCESS_POLICY_TOKEN` (env, set by zshrc) | `Authorization: Bearer <token>` |

Pitfall: `GRAFANA_CLOUD_ACCESS_POLICY_TOKEN` returns **401** on stack/IRM/OnCall API. Always use SA token from TF output for those.

## Bootstrap (every session)

```bash
cd /path/to/terraform/infrastructure/terraform/grafana/<stack>-monitoring
terraform init -input=false -backend=true >/dev/null   # first time only
SA_TOKEN=$(terraform output -raw grafana_sa_token)
INSTANCE_ID=$(terraform output -raw grafana_instance_id)   # <INSTANCE_ID>
STACK_URL=$(terraform output -raw stack_url)               # https://<stack>.grafana.net
ONCALL_URL=$(terraform output -raw oncall_api_url)         # https://<oncall-host>.grafana.net/oncall
```

Other useful outputs:
- `service_account_cicd_id` — CI/CD SA id
- `folder_uids` — Applications / Infrastructure / On-Call
- `team_ids` — engineering / platform
- `gmp_datasource_uid`, `vm_prometheus_datasource_uid`, `vlogs_datasource_uid`
- `oncall_webhook_url` / `oncall_test_webhook_url` (sensitive)

## Curl Pitfalls

- `rtk` tee truncates large bodies in stdout — write to file with `-o /tmp/x.json`, then `jq` the file.
- Always `curl -sS -o <file> ...` for JSON > ~5KB.
- OnCall: `Authorization: <token>` (no `Bearer`).
- Stack: `Authorization: Bearer <token>`.

## Recipes

### Verify IRM plugin enabled
```bash
curl -sS -H "Authorization: Bearer $SA_TOKEN" "$STACK_URL/api/plugins/grafana-irm-app/settings" -o /tmp/irm.json
jq '{id, enabled, version: .info.version}' /tmp/irm.json
```

### List firing alert groups (state=new)
OnCall states: `new` (firing), `acknowledged`, `resolved`, `silenced`. There is no `firing` value — use `new`.

```bash
curl -sS -o /tmp/ag.json \
  -H "Authorization: $SA_TOKEN" -H "X-Grafana-Instance-ID: $INSTANCE_ID" \
  "$ONCALL_URL/api/v1/alert_groups/?state=new&per_page=100"
jq '{count, results: [.results[] | {id, title, alerts_count, created_at, integration_id, route_id}]}' /tmp/ag.json
```

### All alert groups (paginated)
```bash
curl -sS -o /tmp/ag.json \
  -H "Authorization: $SA_TOKEN" -H "X-Grafana-Instance-ID: $INSTANCE_ID" \
  "$ONCALL_URL/api/v1/alert_groups/?per_page=50"
```
Response: `{count, next, previous, results: [...]}`. Follow `next` until null.

### Alert payload for a group
```bash
AG_ID=IQR1MC88VE2RY
curl -sS -o /tmp/al.json \
  -H "Authorization: $SA_TOKEN" -H "X-Grafana-Instance-ID: $INSTANCE_ID" \
  "$ONCALL_URL/api/v1/alerts/?alert_group_id=$AG_ID"
jq '.results[0].payload | {alertname: .labels.alertname, summary: (.commonAnnotations.summary // .annotations.summary // .summary), status, labels}' /tmp/al.json
```

### Acknowledge / Resolve / Silence
```bash
# Ack
curl -sS -X POST -H "Authorization: $SA_TOKEN" -H "X-Grafana-Instance-ID: $INSTANCE_ID" \
  "$ONCALL_URL/api/v1/alert_groups/$AG_ID/acknowledge/"
# Resolve
curl -sS -X POST -H "Authorization: $SA_TOKEN" -H "X-Grafana-Instance-ID: $INSTANCE_ID" \
  "$ONCALL_URL/api/v1/alert_groups/$AG_ID/resolve/"
# Silence (e.g. 3600s)
curl -sS -X POST -H "Authorization: $SA_TOKEN" -H "X-Grafana-Instance-ID: $INSTANCE_ID" \
  -H "Content-Type: application/json" -d '{"delay":3600}' \
  "$ONCALL_URL/api/v1/alert_groups/$AG_ID/silence/"
```

### List integrations / routes / escalation chains
```bash
curl -sS -H "Authorization: $SA_TOKEN" -H "X-Grafana-Instance-ID: $INSTANCE_ID" \
  "$ONCALL_URL/api/v1/integrations/?per_page=100" -o /tmp/int.json
jq '.results[] | {id, name, type, team_id}' /tmp/int.json

curl -sS -H "Authorization: $SA_TOKEN" -H "X-Grafana-Instance-ID: $INSTANCE_ID" \
  "$ONCALL_URL/api/v1/escalation_chains/?per_page=100" -o /tmp/esc.json
```

### Stack-side (managed alerting / contact points / dashboards)
Use Bearer SA token vs `$STACK_URL/api/...`:
```bash
# Folders
curl -sS -H "Authorization: Bearer $SA_TOKEN" "$STACK_URL/api/folders" -o /tmp/f.json
# Datasources
curl -sS -H "Authorization: Bearer $SA_TOKEN" "$STACK_URL/api/datasources" -o /tmp/ds.json
# Provisioned alert rules
curl -sS -H "Authorization: Bearer $SA_TOKEN" "$STACK_URL/api/v1/provisioning/alert-rules" -o /tmp/rules.json
# Contact points
curl -sS -H "Authorization: Bearer $SA_TOKEN" "$STACK_URL/api/v1/provisioning/contact-points" -o /tmp/cp.json
```

Note: Per repo memory, Grafana Cloud has 0 native managed alert rules / 0 contact points — all alerting flows through Alertmanager → OnCall integrations (`gke_alerts` C1AFKGSBQ3ELV, `eks_common_alerts` CPFY985N3P8UQ).

## Known Integration IDs

| Integration | ID | Cloud |
|---|---|---|
| `gke_alerts` | `C1AFKGSBQ3ELV` | GCP |
| `eks_common_alerts` | `CPFY985N3P8UQ` | AWS |

## UI Links

- Stack: https://<stack>.grafana.net
- IRM Alert Groups: https://<stack>.grafana.net/a/grafana-irm-app/alert-groups
- OnCall (legacy app path): https://<stack>.grafana.net/a/grafana-oncall-app/

## Layer Map

- `terraform/grafana/<stack>-monitoring/` — **active** Mumbai stack (dashboards, datasources, OnCall, SAs, folders, teams, SSO).
- `terraform/grafana/<org>/` — **deprecated/broken**, do not modify.
- Decomposition plan: `context/plans/2026-03-05-alerting-decomposition.md` (per-cluster monitoring + per-app layers).
