# Pipeline Security & OIDC Reference

## Why OIDC > Static Keys

- Static IAM keys in repo secrets = credential leakage risk + rotation overhead
- OIDC = cryptographic trust between CI platform and cloud provider
- Credentials auto-expire post-job. Zero permanent access.

## OIDC Flow

1. CI job starts → platform generates JWT (Identity Provider)
2. JWT contains `aud` (audience) + `sub` (subject: repo/branch/tag)
3. Cloud provider validates JWT signature against IdP public keys
4. Evaluates `sub` claim against IAM Role trust policy
5. Returns short-lived STS credentials
6. Credentials expire when job ends

## GitHub Actions OIDC → AWS

```yaml
permissions:
  id-token: write
  contents: read

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: aws-actions/configure-aws-credentials@ec61189 # v6.1.0
      with:
        role-to-assume: arn:aws:iam::123456789012:role/deploy-role
        aws-region: us-east-1
    - run: aws ecs update-service --cluster prod --service api --force-new-deployment
```

## AWS IAM Trust Policy

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {
      "Federated": "arn:aws:iam::123456789012:oidc-provider/token.actions.githubusercontent.com"
    },
    "Action": "sts:AssumeRoleWithWebIdentity",
    "Condition": {
      "StringEquals": {
        "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
      },
      "StringLike": {
        "token.actions.githubusercontent.com:sub": "repo:org/repo:ref:refs/heads/main"
      }
    }
  }]
}
```

Lock `sub` to exact org + repo + branch. Feature branch or fork = JWT rejected.

## GitLab CI OIDC → AWS

```yaml
deploy-production:
  stage: deploy
  image: amazon/aws-cli:2.15.0
  id_tokens:
    GITLAB_OIDC_TOKEN:
      aud: https://gitlab.example.com
  before_script:
    - echo "${GITLAB_OIDC_TOKEN}" > /tmp/web_identity_token
    - |
      echo -e "[profile oidc]\nrole_arn=${AWS_ROLE_ARN}\nweb_identity_token_file=/tmp/web_identity_token" > ~/.aws/config
  script:
    - aws sts get-caller-identity --profile oidc
    - aws ecs update-service --cluster prod --service api --force-new-deployment --profile oidc
```

GitLab trust policy: evaluate `gitlab.com:namespace_id` + `gitlab.com:project_id` (defense against project renaming attacks).

## Poisoned Pipeline Execution (PPE)

| Type | Attack Vector | Mitigation |
|------|--------------|------------|
| Direct PPE (D-PPE) | Malicious PR modifies .gitlab-ci.yml / workflow | Mandatory maintainer approval for external PRs |
| Indirect PPE (I-PPE) | Compromise secondary config repo | Pin config sources, verify integrity |
| Cache Poisoning | Inject malicious binaries into shared cache | Isolate caches between protected/unprotected branches |
| AI Agent PPE | Prompt injection in code comments → agent exfiltrates .env | Human-in-loop for AI PR actions, restrict agent permissions |

## Supply Chain Hardening

- Pin 3rd-party actions to commit SHA (never @v2 tags)
- Trivy / Snyk for container CVE scanning
- Sweet Security: runtime context analysis (is CVE exploitable in deployment target?)
- SonarQube for static code analysis
- SLSA L3 compliance for build provenance
