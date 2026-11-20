# SOC case study — triaging an SSH authentication batch

## Question

Which authentication sequences warrant follow-up, and which source records are needed to interpret the findings?

The [nine-record JSONL input](../examples/synthetic-auth.jsonl) is **synthetic**. All event times, account names, and scores were created for this exercise. The IP addresses are reserved for documentation. The scores are supplied values that exercise the rules. [RFC 5737](https://www.rfc-editor.org/rfc/rfc5737.html)

```text
python -m src.main --input examples/synthetic-auth.jsonl --threshold 0.7 --output reports/synthetic-findings
```

The CLI parsed all nine events and flagged seven. Every flagged record was a failure scored above 0.7. The reports show which rule was applied and its reason. [HTML report](evidence/synthetic-findings.html) · [CSV](evidence/synthetic-findings.csv) · [JSON](evidence/synthetic-findings.json)

## Observed results

| Observed in the run | Analyst follow-up |
| --- | --- |
| **Three high-severity FailedLoginSpike findings.** The three flagged failures for `example-ops` came from `203.0.113.42`. The reason is `>=3 failures for user`. The same IP also meets the repeated-source condition, but the user rule is evaluated first. | Check whether the account and source normally appear together. Review whether legitimate retries, scheduled work, or password guessing could explain the sequence. |
| **Three medium-severity RepeatedSourceIP findings.** Three different accounts had flagged failures from `192.0.2.77`. The reason is `repeated source ip`. | Compare against expected shared egress, infrastructure, and normal account patterns. The repeated address alone cannot identify who initiated the activity. |
| **One medium-severity HighScoreOutlier.** A separate failure with score 0.94 met the score rule. It had no source event timestamp and appears as unknown. | Retrieve the original timestamp, check score provenance, and correlate the event with authentication or endpoint telemetry before assuming an order. |

The source input also contains a successful login for `example-ops` after the failed attempts. It is excluded because detection requires `Failed`, even though its supplied score is 0.98. A failure scored exactly 0.70 is also excluded. To triage the sequence, compare the findings with the full input, then validate the successful session with identity and endpoint records. Neither the success nor the rule label establishes an account compromise.

## Investigation lessons

- **Verify the rule and its inputs.** A severity label reflects rule precedence and the batch available to the tool.
- **Keep excluded evidence available.** A findings-only report can omit events needed to understand the sequence.
- **Document confidence and gaps.** Counts are batch-local. Geographic values are simulated. The exercise contains no real incident or measured detection accuracy.
