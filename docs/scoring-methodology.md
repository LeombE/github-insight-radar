# Scoring Methodology

GitHub Insight scores repositories from 0 to 10 for three target profiles:

- General users
- Data analysts
- Data scientists

The score is a prioritization model, not a claim that one repository is objectively better than another.

## Components

Each profile score uses these components:

| Component | Meaning |
| --- | --- |
| `career_relevance` | How strongly metadata matches the target profile's work. |
| `actionability` | Whether the repository looks suitable for a 30-60 minute review or mini build. |
| `repo_quality` | Repository health signals from stars, forks, license availability, description, and archived status. |
| `momentum` | Recency based on `pushed_at` and `updated_at`. |
| `portfolio_value` | Whether the repository can inspire a case study, dashboard, notebook, automation, or demo. |
| `profile_fit` | Keyword fit for the selected audience. |

## Formula

```text
0.30 * career_relevance
+ 0.20 * actionability
+ 0.15 * repo_quality
+ 0.15 * momentum
+ 0.10 * portfolio_value
+ 0.10 * profile_fit
```

Stars and forks are log-scaled so that popularity helps but does not dominate the ranking.

## Decision Labels

| Score | Decision |
| ---: | --- |
| 8.0-10.0 | Build |
| 6.7-7.99 | Study |
| 5.2-6.69 | Save |
| 0-5.19 | Skip |

## Evidence Boundaries

The GitHub Search API supports metadata such as stars, forks, language, topics, dates, license metadata, and archived status. The system does not infer README quality, installation reliability, or feature completeness from missing evidence.

